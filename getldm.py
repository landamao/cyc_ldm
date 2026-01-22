import random, html, os, aiohttp, json, shutil
from datetime import date
from pypinyin import lazy_pinyin
from astrbot.api.all import logger, asyncio
from astrbot.core.star.star_handler import star_handlers_registry
from astrbot.core.star.filter.command_group import CommandGroupFilter
from astrbot.core.star.filter.command import CommandFilter


class 获取懒大猫:

    def __init__(self):
        #由于运行目录与脚本目录不一致
        self.v当前目录 = os.path.dirname(os.path.abspath(__file__))
        self.v上级目录 = os.path.dirname(self.v当前目录)
        self.v日志目录 = os.path.join(self.v当前目录, '日志信息')
        self.v戳一戳日志文件名 = (os.path.join(self.v日志目录, "今日戳一戳总次数.log"),
                                  os.path.join(self.v上级目录, "今日戳一戳总次数.log"))
        self.v表情包目录 = os.path.join(self.v当前目录, "表情包")
        os.makedirs(self.v日志目录, exist_ok=True)
        os.makedirs(self.v表情包目录, exist_ok=True)
        self.l用户代理池 = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Edge/121.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def f获取实例值(self, 获取值: str):
        for 名, 值 in self.__dict__.items():
            if 名 == 获取值:
                return 值
        return None

    async def f获取百科结果(self, 查询词条: str) -> str:
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

    def f初始化戳一戳日志文件(self) -> int:
        当前日期 = f"当前日期：{date.today().strftime('%Y-%m-%d')}"
        for i in self.v戳一戳日志文件名:
            try:
                try:
                    with open(i, 'r', encoding='utf-8') as f: 文件内容 = f.readlines()
                    文件内容 = [i.strip() for i in 文件内容]

                    if 文件内容[0] != 当前日期: raise FileNotFoundError
                    v今日戳一戳总次数 = int(文件内容[1].strip().split()[-1])
                    logger.info(f"今日戳一戳总次数： {v今日戳一戳总次数}")
                    return v今日戳一戳总次数
                except (IndexError, ValueError):
                    import shutil; shutil.copy(i, i + '.bak')
                    logger.error(f"日志文件格式异常，尝试重置，原文件在{self.v戳一戳日志文件名}.bak"); raise FileNotFoundError
            except FileNotFoundError:  #同时捕获原生的文件不存在和上面需要的重置日志文件
                if i == self.v戳一戳日志文件名[0]: continue
                try:
                    with open(i, 'w', encoding='utf-8') as f:
                        f.write(f"{当前日期}\n今日戳一戳总次数： 0")
                    logger.info(f"今日戳一戳总次数： 0"); return 0
                except Exception as e:  logger.error(f"写入文件发生错误：\n{e}", exc_info=True)
            except Exception as e:  logger.error(f"读取文件发生错误：\n{e}", exc_info=True)

        raise RuntimeError  #前面都没能返回值，那就终止程序

    def f获取表情文件(self, 文件名: str) -> str | None:
        图片后缀 = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
        try:
            for 文件 in os.listdir(self.v表情包目录):
                # 分离文件名和后缀
                名称, 后缀 = os.path.splitext(文件)
                # 检查文件名是否匹配，并且是图片文件
                if 名称 == 文件名 and 后缀.lower() in 图片后缀:
                    return os.path.join(self.v表情包目录, 文件)
            else:
                logger.warning(f"表情名：{文件名}，没有找到这个表情"); return None
        except Exception as e:
            logger.error(f"获取表情文件发生错误\n{e}", exc_info=True); return None

    @staticmethod
    def f获取所有指令(额外指令) -> str:
        #遍历所有注册的处理器获取所有命令，包括别名
        l指令 = []
        for handler in star_handlers_registry:
            for i in handler.event_filters:
                if isinstance(i, CommandFilter):
                    l指令.append(i.command_name)
                    # 获取别名 - 注意属性名是 alias，类型是 set
                    if hasattr(i, 'alias') and i.alias:  l指令.extend(list(i.alias))
                elif isinstance(i, CommandGroupFilter):  l指令.append(i.group_name)

        所有指令 = list(set(l指令)) + 额外指令; 中文指令 = []; 英文指令 = []

        for 指令 in 所有指令:
            if 指令 and '\u4e00' <= 指令[0] <= '\u9fff':  中文指令.append(指令)
            else:  英文指令.append(指令)
        # 排序
        中文指令.sort(key=lambda x: lazy_pinyin(x)); 英文指令.sort(key=lambda x: x.lower())
        # 合并列表
        排序后指令 = 中文指令 + 英文指令
        return '指令使用方法：发送/或./指令\n' + '\n'.join([f"./{i}" for i in 排序后指令]) + f'\n共{len(排序后指令)}个指令，'

    @staticmethod
    def f权重选择器(l权重事件列表: list[str] | tuple[str, ...],
                    l权重值列表: list[int] | tuple[int, ...],
                    v权重和: int | float = None) -> str | None:
        if len(l权重事件列表) != len(l权重值列表): return None
        if v权重和 is None: v权重和 = sum(l权重值列表)
        if v权重和 <= 0: return None

        v累加权重 = 0
        v随机数 = random.uniform(0, v权重和)
        for 事件, 权重 in zip(l权重事件列表, l权重值列表):
            v累加权重 += 权重
            if v随机数 < v累加权重: return 事件

        return None

    def f获取字典数据(self, 字典文件名) -> tuple[dict, dict, dict]:
        """获取三个字典，优先从当前目录读取，如果不存在则从上级目录读取"""
        字典列表 = []

        for 文件名 in 字典文件名:
            当前目录路径 = os.path.join(self.v日志目录, 文件名)
            上级目录路径 = os.path.join(self.v上级目录, 文件名)

            字典数据 = {}

            # 尝试从当前目录读取
            try:
                with open(当前目录路径, 'r', encoding='utf-8') as f:
                    字典数据 = json.load(f)
            except:
            # 如果当前目录没有，尝试从上级目录读取
                try:
                    with open(上级目录路径, 'r', encoding='utf-8') as f:
                        字典数据 = json.load(f)
                    # 将文件复制到当前目录
                    shutil.copy(上级目录路径, 当前目录路径)
                except:
                    pass

            字典列表.append(字典数据)

        return tuple(字典列表)

    @staticmethod
    async def f获取成员信息(event, 获取内容:str = None):  # event：此次消息事件
        """获取内容：
        'group_id': 群号（int）,
        'user_id': （发送者，以下同理）QQ号（int）,
        'nickname': 发送者昵称（str）,
        'card': 标签（str）,
        'sex': 性别（str）,
        'age': 年龄（int）,
        'area': 地区（str）,
        'level': 群内等级（str）,
        'qq_level': 账号等级（int）,
        'join_time': 加入群聊的时间（int）,
        'last_sent_time': 最后发言时间（int）,
        'title_expire_time': 头衔到期时间（int）,
        'unfriendly': 是否被标记为风险用户（bool）,
        'card_changeable': 是否可更换卡片（bool）,
        'is_robot': 是否是机器人账号（bool）,
        'shut_up_timestamp': 禁言结束时间（int）,
        'role': 群内身份（str）,
        'title': 头衔（str），
        类型：<class 'dict'> """
        成员信息: dict = await event.bot.get_group_member_info(
                group_id=event.get_group_id(),
                user_id=event.get_sender_id()
            )
        if 获取内容 is not None:
            return 成员信息.get(获取内容, None)

        return 成员信息

    @staticmethod
    async def f获取成员昵称(event) -> str:
        _ = await event.bot.get_group_member_info(
                group_id=event.get_group_id(),
                user_id=event.get_sender_id()
            )

        return _['nickname']

    @staticmethod
    def f获取预设配置():  #只是个备选方案，修改请移步到“自定义配置.py”
        # 用元组或列表都可以，我是完美主义者，为了稍微提升运行时性能，虽然不多
        被戳回复语 = ( "戳我干嘛呀", "怎么啦", "喵～", "不要戳我啊", "有什么事吗？", "别戳啦~" )

        # 关键词，随机次数范围
        普通 = { "攻击": (2, 3), "猛攻": (3, 4), "戳": (1, 3), "猛揍": (5, 6), "狂揍": (5, 6), "揍他": (5, 6) }

        不回复关键词 = ( "猛揍", "狂揍", "揍他" )  # 写着写着我也不知道是啥了

        管理员限定 = { "肘击": (7, 8), "撞死他": (9, 18), "创死他": (9, 18), "撞大运": (16, 24),
                       "揍死他": (24, 36), "限流": (36, 48), "一键限流": (36, 48) }

        彩蛋 = { "亲亲": (52, 52), "抱抱": (38, 38), "贴贴": (18, 18) }

        关键词次数 = 普通 | 管理员限定 | 彩蛋  # 合并字典，便于获取次数

        冷却话语 = ( "我戳手疼了，晚点再玩嘛。", "够啦够啦，歇会再玩", "不戳啦，歇一会吧" )

        不要戳自己语句 = ( "だめですよ！", "让你戳了吗", "别让我自己戳自己啦，很奇怪的。", "我才不要自己戳自己呢。")

        戳前自嗨语 = ( "收到收到，马上发动攻击！", "好嘞，准备出击！", "没问题，我这就去戳戳Ta！", "收到收到！" )

        管理员语句 = ( "对方已被击灭", "成功击灭对方", "对方被你打倒啦", "对方认输了" )

        戳完回复语 = ( "我厉害叭～", "搞定咯" )

        遵命语 = ( "收到！管理员大大～这就安排！✨", "收到管理员的指令，保证完成任务", "遵命，管理员大大" ) + 戳前自嗨语

        return (被戳回复语, 普通, 不回复关键词, 管理员限定, 彩蛋, 关键词次数, 冷却话语,
                不要戳自己语句, 戳前自嗨语, 管理员语句, 戳完回复语, 遵命语)
