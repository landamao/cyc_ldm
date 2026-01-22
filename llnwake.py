import json
from astrbot.api import logger
async def llm回复(context, event, 提示词: str, ) -> str | None:
    """
    唤醒LLM并获取回复
    参数:
        context，event：在插件环境中，传入相同名字的即可
        提示词: 唤醒提示词
    返回:
        str: LLM的回复内容
        None: 唤醒失败
    """
    logger.info(f"[直接唤醒] 开始唤醒LLM，提示词: {提示词}")

    try:
        # ===================== 第1步: 获取基础数据 =====================
        消息源 = event.unified_msg_origin

        # 获取LLM提供者
        logger.info("[直接唤醒] 获取LLM提供者...")
        LLM提供者 = context.get_using_provider(消息源)
        if not LLM提供者:
            logger.error("[直接唤醒] 未找到可用的LLM提供者")
            return None

        # ===================== 第2步: 获取对话上下文 =====================
        logger.info("[直接唤醒] 获取对话上下文...")
        对话上下文 = await _获取对话上下文(context, 消息源)
        if 对话上下文 is None:
            logger.warning("[直接唤醒] 获取对话上下文失败，使用空上下文")
            对话上下文 = []

        # ===================== 第3步: 获取系统提示词 =====================
        logger.info("[直接唤醒] 获取系统提示词...")
        系统提示词 = await _获取系统提示词(context, 消息源)
        if not 系统提示词:
            logger.warning("[直接唤醒] 获取系统提示词失败，使用默认提示词")
            系统提示词 = "你是一个友好的AI助手。"

        # ===================== 第4步: 调用LLM =====================
        logger.info("[直接唤醒] 调用LLM API...")
        LLM响应 = await LLM提供者.text_chat(
            system_prompt=系统提示词,
            prompt=提示词,
            contexts=对话上下文
        )

        回复内容 = LLM响应.completion_text.strip()
        logger.info(f"[直接唤醒] 成功获取回复，长度: {len(回复内容)}")

        return 回复内容

    except Exception as 异常:
        logger.error(f"[直接唤醒] 唤醒过程失败: {异常}", exc_info=True)
        return None


async def _获取对话上下文(context, 消息源):
    """获取当前对话的上下文历史"""
    try:
        对话管理器 = context.conversation_manager

        # 获取当前会话ID
        当前会话ID = await 对话管理器.get_curr_conversation_id(消息源)
        if not 当前会话ID:
            return []

        # 获取对话对象
        对话 = await 对话管理器.get_conversation(消息源, 当前会话ID)
        if not 对话:
            return []

        # 解析历史记录
        历史上下文 = json.loads(对话.history)
        return 历史上下文

    except Exception as 异常:
        logger.error(f"[直接唤醒] 获取对话上下文失败: {异常}")
        return None


async def _获取系统提示词(context, 消息源):
    """获取当前使用的系统提示词（人格设置）"""
    try:
        from astrbot.core.db.po import Persona, Personality
        对话管理器 = context.conversation_manager

        # 获取当前会话
        当前会话ID = await 对话管理器.get_curr_conversation_id(消息源)
        if not 当前会话ID:
            # 获取默认人格
            默认人格: Personality = await context.persona_manager.get_default_persona_v3(umo=消息源)
            return 默认人格.get("prompt", "")

        对话 = await 对话管理器.get_conversation(消息源, 当前会话ID)
        if not 对话:
            return None

        # 获取人格ID
        人格ID = 对话.persona_id
        if not 人格ID:
            # 使用默认人格
            默认人格: Personality = await context.persona_manager.get_default_persona_v3(umo=消息源)
            return 默认人格.get("prompt", "")

        # 获取指定人格
        人格: Persona = await context.persona_manager.get_persona(persona_id=人格ID)
        return 人格.system_prompt

    except Exception as 异常:
        logger.error(f"[直接唤醒] 获取系统提示词失败: {异常}")
        return None