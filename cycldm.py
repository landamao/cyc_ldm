import random
from datetime import date
import astrbot.api.message_components as Comp
from astrbot.api.all import logger, asyncio
from .getldm import 获取懒大猫
from .llnwake import llm回复

async def f反应戳一戳(self, event, v当前时间):
    v原始消息 = event.message_obj.raw_message; v发戳者ID = v原始消息.get("user_id", 0)

    if str(v发戳者ID) == event.get_self_id(): return
    
    if v当前时间 < self.d反应戳一戳冷却时间.get(v发戳者ID, 0): return

    _f清理冷却字典(self.d反应戳一戳冷却时间, v当前时间)

    self.d反应戳一戳冷却时间[v发戳者ID] = v当前时间 + self.v反应戳一戳冷却时间

    v被戳者ID = v原始消息.get("target_id", 0)
    v机器人ID = v原始消息.get("self_id", 0)
    v群ID = v原始消息.get("group_id", 0)

    v事件 = 获取懒大猫.f权重选择器(self.l权重事件列表, self.tu权重值列表, self.权重和)

    if self.br开启反戳 and v被戳者ID == v机器人ID:
        if v事件 == "回戳": self.v今日戳一戳总次数 += await f发送戳一戳(event, random.randint(1, self.v反戳次数), v群ID, v被戳者ID=v发戳者ID); return
        elif v事件 == "随机回复": yield event.plain_result(random.choice(self.l被戳回复语)); return
        elif v事件 == "llm回复":
            yield event.plain_result(await llm回复(self.context, event,
            f"{self.llm提示词[0]}「{await 获取懒大猫.f获取成员昵称(event)}」{self.llm提示词[1]}"))
        elif v事件 == "不响应": return
        else: return
    elif self.br开启跟戳 and self.v跟戳概率 and random.randint(0, 100) < self.v跟戳概率:
        self.v今日戳一戳总次数 += await f发送戳一戳(event, random.randint(1, self.v反戳次数), v群ID, v被戳者ID); return
    else: return

async def f戳一戳(self, event, v消息文本内容, v消息对象, 当前时间):
    # 获取被艾特用户ID，没有直接退出
    for seg in event.get_messages():
        if isinstance(seg, Comp.At):
            v被艾特用户ID = str(seg.qq)
            v被艾特用户昵称 = str(seg.name)
            break
    else:
        return

    v发送者昵称 = v消息对象.sender.nickname
    v发送者ID = v消息对象.sender.user_id
    br发送者是管理员 = v发送者ID in self.l管理员ID
    br彩蛋 = False
    v自嗨内容 = None  # 确保只自嗨一次

    for 关键词 in self.d普通:
        if v消息文本内容.startswith(关键词):
            event.stop_event()
            break
    else:
        for 关键词 in self.d管理员限定:
            if v消息文本内容.startswith(关键词):
                if not br发送者是管理员: return
                event.stop_event()
                break

        else:
            if self.br开启彩蛋功能:
                for 关键词 in self.d彩蛋:
                    if v消息文本内容.startswith(关键词):
                        br彩蛋 = True
                        break
                else: return
            else: return

    v机器人ID = event.get_self_id()
    v群ID = v消息对象.group_id
    br被艾特者是管理员 = v被艾特用户ID in self.l管理员ID  # 彩蛋特殊处理

    # 检查受击人是否机器人本体
    if v被艾特用户ID == v机器人ID and not br发送者是管理员:
        yield event.plain_result(random.choice(self.l不要戳自己语句))
        
        return

    # 检查是否超过次数
    if fbr达到戳一戳上限(self):
        if br彩蛋:
            if v被艾特用户ID == v机器人ID:
                yield event.plain_result(f"我可不是谁都能{关键词[0]}的")
                return

            yield event.plain_result(f"「{v发送者昵称}」{关键词[0]}了{关键词[1]}「{v被艾特用户昵称}」")

            if 表情文件 := self.获取.f获取表情文件(关键词):
                yield event.make_result().file_image(表情文件)
        else:
            yield event.plain_result("我今日已经戳累啦，明天再玩叭")

        
        return  # 最后退出

    # 检查是否在冷却期
    if self.br管理器无冷却 and br发送者是管理员:
        v自嗨内容 = random.choice(self.l遵命语)

    elif br彩蛋 and 当前时间 < (结束时间 := self.d彩蛋冷却时间.get(v发送者ID, 0)):
        logger.warning(f"用户{v发送者昵称}冷却时间：{结束时间 - 当前时间}秒")
        yield event.plain_result(random.choice(self.l冷却话语))
        
        return

    elif 当前时间 < (结束时间 := self.d用户攻击冷却时间.get(v发送者ID, 0)):
        logger.warning(f"用户{v发送者昵称}冷却时间：{结束时间 - 当前时间}秒")
        yield event.plain_result(random.choice(self.l冷却话语))
        
        return

    if br被艾特者是管理员 and not br彩蛋:  # 检查受击人是否是管理员
        if random.choice([True, True, False]):
            if random.choice([True, False]):
                yield event.plain_result(f"让你戳了吗")
                
                return
            else:
                v自嗨内容 = f"你个{v发送者昵称}也想{关键词}我主人，我这就{关键词}你"; v被戳者ID = v发送者ID
        else:
            v被戳者ID = v被艾特用户ID
    else:
        v被戳者ID = v被艾特用户ID

    # 以上通过，开始攻击
    攻击次数 = random.randint(*self.d关键词次数[关键词])

    if br彩蛋:
        if v被艾特用户ID == v机器人ID: yield event.plain_result(f"我可不是谁都能{关键词[0]}的"); return
        v自嗨内容 = f"「{v发送者昵称}」{关键词}「{v被艾特用户昵称}」{攻击次数}下"
    # 戳前自嗨
    yield event.plain_result(v自嗨内容 if v自嗨内容 else random.choice(self.l戳前自嗨语))

    # 发送戳一戳
    self.v今日戳一戳总次数 += await f发送戳一戳(event, 攻击次数, v群ID, v被戳者ID)

    # 戳完回复
    await asyncio.sleep(0.2)  # 等待一下防止过快
    if br彩蛋 and (表情文件 := self.获取.f获取表情文件(关键词)):
        yield event.make_result().file_image(表情文件)
    elif not br被艾特者是管理员 and 关键词 in self.l不回复关键词:
        yield event.plain_result(random.choice(self.l管理员语句))
    elif random.choice([False, False, True]) or (br发送者是管理员 and not br被艾特者是管理员):
        yield event.plain_result(random.choice(self.l戳完回复语))

    # 设置冷却时间
    # 彩蛋设置超长时间，防止戳一戳次数太快耗完
    if br彩蛋:
        self.d彩蛋冷却时间[v发送者ID] = 当前时间 + self.v彩蛋冷却时间
    else:
        self.d用户攻击冷却时间[v发送者ID] = 当前时间 + random.randint(*self.戳一戳冷却时间)

    _f清理冷却字典(self.d用户攻击冷却时间, 当前时间)
    _f清理冷却字典(self.d彩蛋冷却时间, 当前时间)

    return

async def f发送戳一戳(event, v攻击次数, v群ID, v被戳者ID):
    payloads = {"user_id": v被戳者ID, "group_id": v群ID}
    v当前戳一戳次数 = 0
    logger.info(f"戳{v攻击次数}次")
    for _ in range(v攻击次数):
        await asyncio.sleep(0.02)
        try:
            await event.bot.api.call_action('send_poke', **payloads); v当前戳一戳次数 += 1
        except Exception as e:
            logger.error(f"发送戳一戳失败：\n{e}")

    return v当前戳一戳次数

def fbr达到戳一戳上限(self) -> bool:
    if date.today().day != self.v当前日期:
        self.v当前日期 = date.today().day
        self.v今日戳一戳总次数 = 0
        return False
    return self.v今日戳一戳总次数 > 200

def _f清理冷却字典(字典, 当前时间):
    # 数据太多时删除过期数据
    if len(字典) > 80:
        for i, j in 字典.copy().items():
            if j < 当前时间: del 字典[i]
        
