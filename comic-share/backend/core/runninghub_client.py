"""
RunningHub HTTP 客户端 — 连接测试 / 工作流拉取 / 任务调度 / 图片上传。

工作流规则解析 → core.workflow_analyzer
图片语义推断 → core.image_inferrer
"""

import json
import logging
from typing import Any, Optional

import httpx

from core.config import get_config

logger = logging.getLogger(__name__)

BASE_URL = "https://www.runninghub.cn"

# ── 内部工具 ─────────────────────────────────────────────


def _get_rh_config() -> dict:
    """获取 runninghub 配置段。"""
    return get_config().get("runninghub", {})


def _get_active_key() -> str:
    """获取当前激活的 API Key。"""
    rh = _get_rh_config()
    key_type = rh.get("active_key_type", "consumer")
    return rh.get("keys", {}).get(key_type, "")


def _get_proxy() -> Optional[str]:
    """获取代理地址（未启用时返回 None）。"""
    rh = _get_rh_config()
    if rh.get("proxy_enabled", False):
        return rh.get("proxy", "") or None
    return None


def _make_client(timeout: int = 60) -> httpx.Client:
    """创建带代理的 httpx 同步客户端。"""
    proxy = _get_proxy()
    return httpx.Client(timeout=timeout, proxy=proxy if proxy else None)


def _make_headers(api_key: str) -> dict:
    """构造 RunningHub 请求头。"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Host": "www.runninghub.cn",
    }


def _unwrap_workflow_data(raw: Any) -> dict:
    """统一解包 getJsonApiFormat 返回的 data 字段为节点字典。"""
    if raw is None:
        return {}
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        return {}
    if not isinstance(raw, dict):
        return {}

    sample_key = next(iter(raw), None)
    if sample_key is not None:
        sample_val = raw[sample_key]
        if isinstance(sample_val, dict) and "class_type" in sample_val:
            return raw

    if len(raw) == 1:
        inner = next(iter(raw.values()))
        if isinstance(inner, str):
            try:
                parsed = json.loads(inner)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
        elif isinstance(inner, dict):
            inner_sample = next(iter(inner.values()), None)
            if isinstance(inner_sample, dict) and "class_type" in inner_sample:
                return inner

    return raw


# ── 公开 API ─────────────────────────────────────────────


def test_connection(api_key: Optional[str] = None) -> dict:
    """测试 API Key 连通性。"""
    key = api_key or _get_active_key()
    if not key:
        return {"ok": False, "message": "API Key 为空"}
    try:
        with _make_client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/task/openapi/create",
                headers=_make_headers(key),
                json={"apiKey": key, "workflowId": "0"},
            )
            data = resp.json()
            code = data.get("code")
            if code in (0, 380):
                return {"ok": True, "message": f"API Key 有效 (code={code})"}
            if code == 801:
                return {"ok": False, "message": "免费用户不支持 API，请升级会员"}
            if code == 412:
                return {"ok": False, "message": "API Key 无效或 URL 拼写错误"}
            return {"ok": False, "message": f"未知响应: code={code}"}
    except httpx.TimeoutException:
        return {"ok": False, "message": "连接超时，请检查代理设置"}
    except Exception as e:
        return {"ok": False, "message": f"连接异常: {e}"}


def fetch_workflow_json(workflow_id: str, api_key: Optional[str] = None) -> dict:
    """获取工作流的完整节点 JSON。"""
    key = api_key or _get_active_key()
    if not key:
        return {"ok": False, "data": None, "message": "API Key 为空"}
    try:
        with _make_client(timeout=30) as client:
            resp = client.post(
                f"{BASE_URL}/api/openapi/getJsonApiFormat",
                headers=_make_headers(key),
                json={"apiKey": key, "workflowId": workflow_id},
            )
            data = resp.json()
            if data.get("code") == 0:
                nodes = _unwrap_workflow_data(data.get("data"))
                logger.info("[fetch] workflow=%s, nodes=%d", workflow_id, len(nodes))
                return {"ok": True, "data": nodes, "message": "success"}
            if data.get("code") == 404:
                return {"ok": False, "data": None,
                        "message": f"工作流 {workflow_id} 不存在"}
            return {"ok": False, "data": None,
                    "message": f"code={data.get('code')}, msg={data.get('msg', '')}"}
    except Exception as e:
        return {"ok": False, "data": None, "message": str(e)}


def create_task(
    workflow_id: str,
    node_info_list: Optional[list[dict]] = None,
    api_key: Optional[str] = None,
) -> dict:
    """提交 RunningHub 任务。"""
    key = api_key or _get_active_key()
    if not key:
        return {"ok": False, "taskId": "", "taskStatus": "", "message": "API Key 为空"}

    payload: dict[str, Any] = {"apiKey": key, "workflowId": workflow_id}
    if node_info_list:
        payload["nodeInfoList"] = node_info_list

    try:
        with _make_client(timeout=30) as client:
            resp = client.post(
                f"{BASE_URL}/task/openapi/create",
                headers=_make_headers(key),
                json=payload,
            )
            data = resp.json()
            if data.get("code") == 0:
                task_data = data.get("data", {})
                return {
                    "ok": True,
                    "taskId": task_data.get("taskId", ""),
                    "taskStatus": task_data.get("taskStatus", "QUEUED"),
                    "message": "success",
                }
            return {
                "ok": False, "taskId": "", "taskStatus": "",
                "message": f"code={data.get('code')}, msg={data.get('msg', '')}",
            }
    except Exception as e:
        return {"ok": False, "taskId": "", "taskStatus": "", "message": str(e)}


def poll_task_status(task_id: str, api_key: Optional[str] = None) -> dict:
    """查询任务状态（单次，不循环）。"""
    key = api_key or _get_active_key()
    payload = {"apiKey": key, "taskId": task_id}

    try:
        with _make_client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/task/openapi/outputs",
                headers=_make_headers(key),
                json=payload,
            )
            data = resp.json()
            code = data.get("code")
            if code == 0:
                return {"status": "COMPLETED", "outputs": data.get("data", []),
                        "message": "success"}
            if code in (813, 812):
                return {"status": "QUEUED", "outputs": [], "message": "排队中"}
            if code == 804:
                return {"status": "RUNNING", "outputs": [], "message": "运行中"}
            return {"status": "FAILED", "outputs": [],
                    "message": f"code={code}, msg={data.get('msg', '')}"}
    except Exception as e:
        return {"status": "FAILED", "outputs": [], "message": str(e)}


def cancel_task(task_id: str, api_key: Optional[str] = None) -> dict:
    """取消任务。"""
    key = api_key or _get_active_key()
    try:
        with _make_client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/task/openapi/cancel",
                headers=_make_headers(key),
                json={"apiKey": key, "taskId": task_id},
            )
            data = resp.json()
            return {"ok": data.get("code") == 0, "message": data.get("msg", "")}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def upload_image(file_bytes: bytes, filename: str,
                 api_key: Optional[str] = None) -> dict:
    """上传图片到 RunningHub。"""
    key = api_key or _get_active_key()
    try:
        proxy = _get_proxy()
        with httpx.Client(timeout=60, proxy=proxy if proxy else None) as client:
            resp = client.post(
                f"{BASE_URL}/task/openapi/upload",
                data={"apiKey": key},
                files={"file": (filename, file_bytes)},
                headers={"Authorization": f"Bearer {key}"},
            )
            data = resp.json()
            if data.get("code") == 0:
                return {"ok": True, "fileName": data["data"]["fileName"],
                        "message": "success"}
            return {"ok": False, "fileName": "", "message": data.get("msg", "")}
    except Exception as e:
        return {"ok": False, "fileName": "", "message": str(e)}
