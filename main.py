import random, time, html, os, aiohttp
from pypinyin import lazy_pinyin
import astrbot.api.message_components as Comp
from astrbot.api.all import logger, register, Star, EventMessageType, asyncio, event_message_type
from astrbot.core import AstrBotConfig; from astrbot.core.message.components import Poke
from astrbot.core.star.star_handler import star_handlers_registry; from astrbot.core.star import Context
from astrbot.core.star.filter.command_group import CommandGroupFilter
from astrbot.core.star.filter.command import CommandFilter
from astrbot.api.event import filter, AstrMessageEvent

@register("多功能戳一戳", "懒大猫", "多种戳一戳功能", "9.9.9", "")
class 戳一戳懒大猫(Star):
    #初始化只会执行一次，写再冗余都不会浪费性能
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        # 读取配置
        try:
            from .自定义配置 import 配置
            self.l被戳回复语 = 配置.戳完回复语; self.d普通 = 配置.普通; self.l不回复关键词 = 配置.不回复关键词
            self.d限定 = 配置.管理员限定; self.d彩蛋 = 配置.彩蛋; self.d关键词次数 = 配置.关键词次数
            self.l冷却话语 = 配置.冷却话语; self.l不要戳自己语句 = 配置.不要戳自己语句; self.l戳前自嗨语 = 配置.戳前自嗨语
            self.l管理员语句 = 配置.管理员语句; self.l戳完回复语 = 配置.戳完回复语; self.l遵命语 = 配置.遵命语
            logger.info("载入自定义配置成功")
        except Exception as e:  #失败直接退回预设配置
            logger.error(f"载入配置失败，请确保配置文件存在且格式正确\n{e}", exc_info=True)
            logger.warning("\n\n注意：已使用预设配置")

            #用元组或列表都可以，我是完美主义者，为了稍微提升运行时性能，虽然不多
            self.l被戳回复语 = ("戳我干嘛呀", "怎么啦", "喵～", "不要戳我啊", "有什么事吗？", "别戳啦~")
            # 关键词，随机次数范围
            self.d普通 = {"攻击": (2, 3), "猛攻": (3, 4), "戳": (1, 3), "猛揍": (5, 6), "狂揍": (5, 6), "揍他": (5, 6)}

            self.l不回复关键词 = ("猛揍", "狂揍", "揍他")

            self.d限定 = {"肘击": (7, 8), "撞死他": (9, 18), "创死他": (9, 18), "撞大运": (16, 24), "揍死他": (24, 36),
                          "限流": (36, 48), "一键限流": (36, 48)}

            self.d彩蛋 = {"亲亲": (52, 52), "抱抱": (38, 38)}

            self.d关键词次数 = self.d普通 | self.d限定 | self.d彩蛋

            self.l冷却话语 = ("我戳手疼了，晚点再玩嘛。", "够啦够啦，歇会再玩", "不戳啦，歇一会吧")

            self.l不要戳自己语句 = ("だめですよ！", "让你戳了吗", "别让我自己戳自己啦，很奇怪的。",
                                    "我才不要自己戳自己呢。")

            self.l戳前自嗨语 = ("收到收到，马上发动攻击！", "好嘞，准备出击！", "没问题，我这就去戳戳Ta！", "收到收到！")

            self.l管理员语句 = ("对方已被击灭", "成功击灭对方", "对方被你打倒啦", "对方认输了")

            self.l戳完回复语 = ("我厉害叭～", "搞定咯")

            self.l遵命语 = ("收到！管理员大大～这就安排！✨", "收到管理员的指令，保证完成任务",
                            "遵命，管理员大大") + self.l戳前自嗨语

        #读取配置
        self.br开启百度百科 = config['百度百科']; self.br戳一戳 = config['戳一戳']
        self.br管理器无冷却 = config['管理员无冷却']; self.br开启跟戳 = config['跟戳']; self.br开启反戳 = config['被戳']
        self.l关键词戳一戳 = tuple([ i.strip() for i in config['关键词戳一戳'].replace("，", ",").split(",") ])
        #这几项为字符串填写，需捕获错误
        try: self.戳一戳冷却时间 = tuple(map(int, config['戳一戳冷却时间'].strip().replace("，", ",").split(",")))
        except: logger.error("戳一戳冷却时间填写有误，使用默认值20, 60"); self.戳一戳冷却时间 = (20, 60)
        self.br指令菜单 = config['指令菜单'].replace('开', '1').replace('关', '0')
        try: #转成整数便于判断也便于判断填写格式是否正确
            if config['指令菜单'][0] == "0": self.br指令菜单 = (0,0)
            self.br指令菜单 = tuple(map(int,self.br指令菜单.strip().replace("，",",").split(",")))
        except: logger.error("指令菜单开关格式填写有误，使用默认值开, 关"); self.br指令菜单 = (1,0)

        try: self.tu权重值列表 = tuple(map(int, config['被戳反应权重'].strip().replace("，", ",").split(",")))
        except: logger.error("被戳反应权重填写有误，使用默认值5, 5, 2"); self.tu权重值列表 = (5, 5, 2)
        self.br开启彩蛋功能 = config['彩蛋功能']; self.v彩蛋冷却时间 = config['彩蛋冷却时间']
        self.l权重事件列表 = ('回戳', '随机回复', '不响应')
        self.权重和 = sum(self.tu权重值列表); self.v跟戳概率 = config['跟戳概率'] * 100
        self.v反应戳一戳冷却时间 = config['反应戳一戳冷却时间']; self.v反戳次数 = config['反戳次数']
        self.l黑名单用户 = tuple(config['黑名单用户'])
        self.l管理员ID = tuple([ i for i in self.context.get_config()['admins_id'] ])

        if self.br指令菜单[0]: self.v所有指令 = self._f格式化指令()

        # 由于每日戳一戳上限为200次
        #由于运行目录与脚本目录不一致
        self.v当前目录 = os.path.dirname(os.path.abspath(__file__))
        self.v戳一戳日志文件名 = os.path.join(self.v当前目录, "今日戳一戳总次数.log")
        self.v表情包目录 = os.path.join(self.v当前目录, "表情包")
        os.makedirs(self.v表情包目录, exist_ok=True)
        self.v今日戳一戳总次数 = self._f初始化戳一戳日志文件()

        self.l用户代理池 = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Edge/121.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.d用户攻击冷却时间 = {};  self.d反应戳一戳冷却时间 = {}; self.d彩蛋冷却时间 = {}

        [ logger.info(f'{i}：{j}') for i, j in config.items() ]; logger.info('加载完成')

    @event_message_type(EventMessageType.GROUP_MESSAGE, priority=96)
    async def f主函数处理消息(self, event: AstrMessageEvent):  # 主函数

        v消息文本内容 = event.message_str

        if self.br开启百度百科 and v消息文本内容.startswith("百度百科") and len(v消息文本内容) > 4:
            event.stop_event(); v搜索词条 = v消息文本内容[4:].strip()
            if len(v搜索词条) > 30:
                yield event.plain_result("词条过长"); return
            if v搜索词条:
                百科结果 = await self.f调用百度百科API(v搜索词条); yield event.plain_result(百科结果)
            return

        if event.get_sender_id() in self.l黑名单用户: return  #在黑名单以下全部不响应

        v消息对象 = event.message_obj; 当前时间 = time.time()

        if event.message_obj.message and isinstance(event.message_obj.message[0], Poke):
            if not self.br开启跟戳 and not self.br开启反戳:
                return
            event.stop_event()
            if self.v今日戳一戳总次数 > 200:
                logger.warning("今日戳一戳已达上限"); return
            async for i in self.f反应戳一戳(event, 当前时间): yield i

        if not v消息文本内容: return

        if any( i in v消息文本内容 for i in self.l关键词戳一戳 ):
            v发送者ID = v消息对象.sender.user_id; v群ID = v消息对象.group_id
            await self.f发送戳一戳(event, random.randint(1, self.v反戳次数), v群ID, v被戳者ID=v发送者ID)
            return

        # 戳一戳部分
        if not self.br戳一戳: return

        async for i in self.f戳一戳(event, v消息文本内容, v消息对象, 当前时间): yield i
        return

    @filter.command("指令菜单")
    async def f指令菜单(self, event: AstrMessageEvent):
        event.stop_event(); event.should_call_llm(False)
        if not self.br指令菜单[0]: return
        if self.br指令菜单[1] and not event.is_admin(): return
        yield event.plain_result(self.v所有指令); return

    @filter.command("戳一戳次数")
    @filter.permission_type(filter.PermissionType.ADMIN, raise_error=False)
    async def f查看戳一戳次数(self, event: AstrMessageEvent):
        yield event.plain_result(f"今日戳一戳次数：{self.v今日戳一戳总次数}"); return

    @staticmethod
    def _f清理冷却字典(字典, 当前时间):
        for i, j in 字典.copy().items():  # 细节修正：使用浅拷贝避免发生错误
            if j < 当前时间: del 字典[i]

    def _f初始化戳一戳日志文件(self) -> int:
        当前日期 = f"当前日期：{time.strftime('%Y-%m-%d', time.localtime(time.time()))}"
        try:
            try:
                with open(self.v戳一戳日志文件名, 'r', encoding='utf-8') as f: 文件内容 = f.readlines()
                文件内容 = [i.strip() for i in 文件内容]

                if 文件内容[0] != 当前日期:
                    """重置日志文件，AI都会说这里不合理，但这很精妙，
                    与下面的格式错误区分日志提示，统一交给文件不存在处理，比再写一个重置函数代码量更少，结果更紧凑"""
                    raise FileNotFoundError
                v今日戳一戳总次数 = int(文件内容[1].strip().split()[-1])
                logger.info(f"今日戳一戳总次数： {v今日戳一戳总次数}")
                return v今日戳一戳总次数
            except (IndexError, ValueError):
                import shutil; shutil.copy(self.v戳一戳日志文件名, self.v戳一戳日志文件名 + '.bak')
                logger.error(f"日志文件格式异常，尝试重置，原文件在{self.v戳一戳日志文件名}.bak"); raise FileNotFoundError
        except FileNotFoundError:  #同时捕获原生的文件不存在和上面需要的重置日志文件
            try:
                with open(self.v戳一戳日志文件名, 'w', encoding='utf-8') as f:
                    f.write(f"{当前日期}\n今日戳一戳总次数： 0")
                logger.info(f"今日戳一戳总次数： 0"); return 0
            except Exception as e:  logger.error(f"写入文件发生错误：\n{e}", exc_info=True)
        except Exception as e:  logger.error(f"读取文件发生错误：\n{e}", exc_info=True)
        raise RuntimeError  #前面都没能返回值，那就终止程序

    async def _f同步戳一戳次数(self, 增加的戳一戳次数: int):
        try:
            当前日期 = f"当前日期：{time.strftime('%Y-%m-%d', time.localtime(time.time()))}"

            with open(self.v戳一戳日志文件名, 'r+', encoding='utf-8') as f:
                文件内容 = f.readlines(); 文件内容 = [ i.strip() for i in 文件内容 ]
                if 文件内容[0].strip() != 当前日期:  文件内容[0] = 当前日期; self.v今日戳一戳总次数 = 0

                self.v今日戳一戳总次数 += 增加的戳一戳次数
                文件内容[1] = f"今日戳一戳总次数： {self.v今日戳一戳总次数}"

                f.seek(0); f.truncate(); f.write('\n'.join(文件内容))

            logger.info('\t'.join(文件内容))

        except Exception as e:
            logger.error(f"当前戳一戳总次数：{self.v今日戳一戳总次数}\n保存日志发送错误：\n{e}", exc_info=True)
        
    @staticmethod
    def _f获取所有指令() -> list[str]:
        #遍历所有注册的处理器获取所有命令，包括别名
        l指令 = []
        for handler in star_handlers_registry:
            for i in handler.event_filters:
                if isinstance(i, CommandFilter):
                    l指令.append(i.command_name)
                    # 获取别名 - 注意属性名是 alias，类型是 set
                    if hasattr(i, 'alias') and i.alias:  l指令.extend(list(i.alias))
                elif isinstance(i, CommandGroupFilter):  l指令.append(i.group_name)
        # 去重并返回
        return list(set(l指令))

    def _f格式化指令(self) -> str:
        所有指令 = self._f获取所有指令(); 中文指令 = []; 英文指令 = []

        for 指令 in 所有指令:
            if 指令 and '\u4e00' <= 指令[0] <= '\u9fff':  中文指令.append(指令)
            else:  英文指令.append(指令)
        # 排序
        中文指令.sort(key=lambda x: lazy_pinyin(x)); 英文指令.sort(key=lambda x: x.lower())
        # 合并列表
        排序后指令 = 中文指令 + 英文指令
        return '指令使用方法：发送/或./指令\n' + '\n'.join([f"./{i}" for i in 排序后指令])

    async def f调用百度百科API(self, 查询词条: str) -> str:
        api地址 = "https://oiapi.net/api/BaiduEncyclopedia"; 参数 = {"msg": 查询词条}
        代理 = random.choice(self.l用户代理池)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get( url=api地址, params=参数, headers={
                            "User-Agent": 代理},
                            timeout=aiohttp.ClientTimeout(total=10)
                ) as 响应:
                    响应.raise_for_status(); 接口数据 = await 响应.json()
                    if not 接口数据.get("data"):  return f"「{查询词条}」百度百科暂未收录该词条"
                    data = 接口数据["data"]
                    搜索词条名 = html.unescape(data.get("search", "未知词条"))
                    词条简介 = html.unescape(data.get("result", "无简介"))
                    百科链接 = html.unescape(data.get("url", "无详情页链接"))

                    最大字数 = 600; 简介 = 词条简介[:最大字数] + "..." if len(词条简介) > 最大字数 else 词条简介

                    return f"搜索词条：{搜索词条名}\n\n{简介}\n\n详情页：{百科链接}"

        except asyncio.TimeoutError:  return "请求超时"
        except aiohttp.ClientError as e:  logger.error(f"网络请求错误：\n{e}"); return "搜索失败"
        except Exception as e:  logger.error(f"搜索失败：\n{e}", exc_info=True); return "搜索失败"

    async def f戳一戳(self, event, v消息文本内容, v消息对象, 当前时间):
        #获取被艾特用户ID，没有直接退出
        for seg in event.get_messages():
            if isinstance(seg, Comp.At):
                v被艾特用户ID = str(seg.qq)
                v被艾特用户昵称 = str(seg.name)
                break
        else:  return

        v发送者昵称 = v消息对象.sender.nickname
        v发送者ID = v消息对象.sender.user_id
        br发送者是管理员 = v发送者ID in self.l管理员ID
        br彩蛋 = False; v自嗨内容 = None  # 确保只自嗨一次

        for 关键词 in self.d普通:
            if v消息文本内容.startswith(关键词):
                event.stop_event(); break
        else:
            for 关键词 in self.d限定:
                if v消息文本内容.startswith(关键词):
                    if not br发送者是管理员:
                        event.should_call_llm(False); return
                    event.stop_event(); break

            else:
                if self.br开启彩蛋功能:
                    for 关键词 in self.d彩蛋:
                        if v消息文本内容.startswith(关键词):
                            br彩蛋 = True; break
                    else: return
                else: return

        v机器人ID = event.get_self_id()
        v群ID = v消息对象.group_id
        br被艾特者是管理员 = v被艾特用户ID in self.l管理员ID  #彩蛋特殊处理

        # 检查受击人是否机器人本体
        if v被艾特用户ID == v机器人ID and not br发送者是管理员:
            yield event.plain_result(random.choice(self.l不要戳自己语句)); event.should_call_llm(False); return

        # 检查是否超过次数
        if self.v今日戳一戳总次数 > 200:
            if br彩蛋:
                if v被艾特用户ID == v机器人ID: yield event.plain_result(f"我可不是谁都能{关键词[0]}的"); return
                yield event.plain_result(f"「{v发送者昵称}」{关键词[0]}了{关键词[1]}「{v被艾特用户昵称}」")
                if 表情文件 := self._f发送表情(关键词): yield event.make_result().file_image(表情文件)
            else: yield event.plain_result("我今日已经戳累啦，明天再玩叭")
            event.should_call_llm(False); return  #最后退出

        # 检查是否在冷却期
        if self.br管理器无冷却 and br发送者是管理员:  v自嗨内容 = random.choice(self.l遵命语)
        elif 当前时间 < (结束时间 := self.d彩蛋冷却时间.get(v发送者ID, 0)):
            logger.warning(f"用户{v发送者昵称}冷却时间：{结束时间 - 当前时间}秒")
            yield event.plain_result(random.choice(self.l冷却话语)); event.should_call_llm(False); return
        elif 当前时间 < (结束时间 := self.d用户攻击冷却时间.get(v发送者ID, 0)):
            logger.warning(f"用户{v发送者昵称}冷却时间：{结束时间 - 当前时间}秒")
            yield event.plain_result(random.choice(self.l冷却话语)); event.should_call_llm(False); return

        if br被艾特者是管理员 and not br彩蛋:  # 检查受击人是否是管理员
            if random.choice([True, True, False]):
                if random.choice([True, False]):  
                    yield event.plain_result(f"让你戳了吗"); event.should_call_llm(False); return
                else:  v自嗨内容 = f"你个{v发送者昵称}也想{关键词}我主人，我这就{关键词}你"; v被戳者ID = v发送者ID
            else: v被戳者ID = v被艾特用户ID
        else: v被戳者ID = v被艾特用户ID

        #以上通过，开始攻击
        攻击次数 = random.randint(*(self.d关键词次数|self.d限定)[关键词])

        if br彩蛋:
            if v被艾特用户ID == v机器人ID: yield event.plain_result(f"我可不是谁都能{关键词[0]}的"); return
            v自嗨内容 = f"「{v发送者昵称}」{关键词}「{v被艾特用户昵称}」{攻击次数}下"
        # 戳前自嗨
        yield event.plain_result(v自嗨内容 if v自嗨内容 else random.choice(self.l戳前自嗨语))

        # 发送戳一戳
        await self.f发送戳一戳(event, 攻击次数, v群ID, v被戳者ID)

        # 戳完回复
        await asyncio.sleep(0.2)  # 等待一下防止过快
        if br彩蛋 and (表情文件 := self._f发送表情(关键词)):
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
        # 数据太多时删除过期数据
        if len(self.d用户攻击冷却时间) > 100: self._f清理冷却字典(self.d用户攻击冷却时间, 当前时间)
        if len(self.d彩蛋冷却时间) > 100: self._f清理冷却字典(self.d彩蛋冷却时间, 当前时间)

        return

    def _f发送表情(self, 表情名: str) -> str | None:
        if 表情文件 := self._f获取表情包文件(表情名):
            try:
                return 表情文件
            except Exception as e:
                logger.error(f"发送表情发生错误：\n{e}", exc_info=True)
        else: logger.warning(f"表情名：{表情名}，没有找到这个表情"); return None

    def _f获取表情包文件(self, 文件名: str) -> str | None:
        图片后缀 = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')

        if not os.path.exists(self.v表情包目录):
            return None

        for 文件 in os.listdir(self.v表情包目录):
            # 分离文件名和后缀
            名称, 后缀 = os.path.splitext(文件)
            # 检查文件名是否匹配，并且是图片文件
            if 名称 == 文件名 and 后缀.lower() in 图片后缀:
                return os.path.join(self.v表情包目录, 文件)

        return None

    async def f发送戳一戳(self, event, v攻击次数, v群ID, v被戳者ID):
        payloads = {"user_id": v被戳者ID, "group_id": v群ID}; v当前戳一戳次数 = 0; logger.info(f"戳{v攻击次数}次")
        for _ in range(v攻击次数):
            await asyncio.sleep(0.02)
            try: await event.bot.api.call_action('send_poke', **payloads); v当前戳一戳次数 += 1
            except Exception as e: logger.error(f"发送戳一戳失败：\n{e}")

        await self._f同步戳一戳次数(增加的戳一戳次数=v当前戳一戳次数)

    @staticmethod
    def f权重选择器(l权重事件列表: list[str] | tuple[str, ...],
                    l权重值列表: list[int] | tuple[int, ...],
                    v权重和: int | float = None) -> str | None:
        if len(l权重事件列表) != len(l权重值列表): return None
        if v权重和 is None: v权重和 = sum(l权重值列表)
        if v权重和 <= 0: return None

        v累加权重 = 0; v随机数 = random.uniform(0, v权重和)
        for 事件, 权重 in zip(l权重事件列表, l权重值列表):
            v累加权重 += 权重
            if v随机数 < v累加权重: return 事件

        return None

    async def f反应戳一戳(self, event, v当前时间):
        v原始消息 = event.message_obj.raw_message; v发戳者ID = v原始消息.get("user_id", 0)

        if v当前时间 < self.d反应戳一戳冷却时间.get(v发戳者ID, 0): return
        if len(self.d反应戳一戳冷却时间) > 100: self._f清理冷却字典(self.d反应戳一戳冷却时间, v当前时间)
        self.d反应戳一戳冷却时间[v发戳者ID] = v当前时间 + self.v反应戳一戳冷却时间

        v被戳者ID = v原始消息.get("target_id", 0); v机器人ID = v原始消息.get("self_id", 0); v群ID = v原始消息.get("group_id", 0)

        v事件 = self.f权重选择器(self.l权重事件列表, self.tu权重值列表, self.权重和)

        if v发戳者ID == v机器人ID: return

        if self.br开启反戳 and v被戳者ID == v机器人ID:
            if v事件 == "回戳": await self.f发送戳一戳(event, random.randint(1, self.v反戳次数), v群ID, v被戳者ID=v发戳者ID); return
            elif v事件 == "随机回复": yield event.plain_result(random.choice(self.l被戳回复语)); return
            elif v事件 == "不响应": return
            else: return
        elif self.br开启跟戳 and self.v跟戳概率 and random.randint(0, 100) < self.v跟戳概率:
            await self.f发送戳一戳(event, random.randint(1, self.v反戳次数), v群ID, v被戳者ID); return
        else: return
