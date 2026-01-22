import os, time, shutil, json
from astrbot.api.all import Star, EventMessageType, event_message_type
from astrbot.core import AstrBotConfig; from astrbot.core.message.components import Poke
from astrbot.core.star import Context
from astrbot.api.event import filter, AstrMessageEvent
from .cycldm import *  #文件名用中文可能出现乱码，但是代码内容不会



class 懒大猫(Star):


    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context

        #初始化只执行一次，怎么牛逼怎么来
        """初始获取类"""
        self.获取 = 获取懒大猫()
        self.v当前日期 = date.today().day
        self.v当前目录 = self.获取.f获取实例值('v当前目录')
        self.v上级目录 = self.获取.f获取实例值('v上级目录')
        self.v日志目录 = self.获取.f获取实例值('v日志目录')
        self.v戳一戳日志文件名 = self.获取.f获取实例值('v戳一戳日志文件名')

        """读取设定配置"""
        self.br开启百度百科 = config['百度百科']

        #========读取指令菜单相关========
        self.br指令菜单 = config['指令菜单'].replace('开', '1').replace('关', '0')
        try: #转成整数便于判断也便于判断填写格式是否正确
            if config['指令菜单'][0] == "0": self.br指令菜单 = (0,0)
            self.br指令菜单 = tuple(map(int,self.br指令菜单.strip().replace("，",",").split(",")))
        except: logger.error("指令菜单开关格式填写有误，使用默认值开, 关"); self.br指令菜单 = (1,0)
        #预先获取所有指令
        if self.br指令菜单[0]: self.v所有指令 = self.获取.f获取所有指令(config['额外指令'].copy())

        #========获取彩蛋相关========
        self.br开启彩蛋功能 = config['彩蛋功能']; self.v彩蛋冷却时间 = config['彩蛋冷却时间']

        #========获取反应戳一戳相关========
        self.l权重事件列表 = ('回戳', '随机回复', 'llm回复', '不响应')
        try:
            self.tu权重值列表 = tuple(map(int, config['被戳反应权重'].strip().replace("，", ",").split(",")))
            if len(self.tu权重值列表) != len(self.l权重事件列表): raise ValueError
        except: logger.error("被戳反应权重填写有误，使用默认值5, 4, 4, 2"); self.tu权重值列表 = (5, 4, 4, 2)

        self.br开启跟戳 = config['跟戳']; self.br开启反戳 = config['被戳']
        self.权重和 = sum(self.tu权重值列表); self.v跟戳概率 = config['跟戳概率'] * 100
        self.v反应戳一戳冷却时间 = config['反应戳一戳冷却时间']; self.v反戳次数 = config['反戳次数']
        self.l关键词戳一戳 = tuple([ i.strip() for i in config['关键词戳一戳'].replace("，", ",").split(",") ])
        self.llm提示词 = tuple(config['llm提示词'].strip().split('{昵称}'))

        #========获取其他========
        self.l黑名单用户 = tuple([ i.strip() for i in config['黑名单用户']])
        self.l管理员ID = tuple([ i.strip() for i in self.context.get_config()['admins_id'] ])

        #========读取戳一戳相关========
        self.v今日戳一戳总次数 = self.获取.f初始化戳一戳日志文件()
        self.br戳一戳 = config['戳一戳']; self.br管理器无冷却 = config['管理员无冷却']

        try: self.戳一戳冷却时间 = tuple(map(int, config['戳一戳冷却时间'].strip().replace("，", ",").split(",")))
        except: logger.error("戳一戳冷却时间填写有误，使用默认值20, 60"); self.戳一戳冷却时间 = (20, 60)

        for i, j in config.items(): logger.info(f'{i}：{j}')

        """读取自定义配置"""
        try:  #捕获可能修改时出现的语法错误等
            from .自定义配置 import 配置
            self.l被戳回复语 = 配置.被戳回复语; self.d普通 = 配置.普通; self.l不回复关键词 = 配置.不回复关键词
            self.d管理员限定 = 配置.管理员限定; self.d彩蛋 = 配置.彩蛋; self.d关键词次数 = 配置.关键词次数
            self.l冷却话语 = 配置.冷却话语; self.l不要戳自己语句 = 配置.不要戳自己语句; self.l戳前自嗨语 = 配置.戳前自嗨语
            self.l管理员语句 = 配置.管理员语句; self.l戳完回复语 = 配置.戳完回复语; self.l遵命语 = 配置.遵命语
            logger.info("加载自定义配置成功")
        except Exception as e:  #失败直接退回预设配置
            logger.error(f"加载自定义配置失败，请确保配置文件存在且格式正确，请分享错误信息给AI获取修正\n{e}", exc_info=True)
            logger.warning("\n\n注意：已使用预设配置\n\n")
            (self.l被戳回复语, self.d普通, self.l不回复关键词, self.d管理员限定, self.d彩蛋, self.d关键词次数,
             self.l冷却话语, self.l不要戳自己语句, self.l戳前自嗨语, self.l管理员语句, self.l戳完回复语,
             self.l遵命语) = 获取懒大猫.f获取预设配置

        #获取冷却字典
        self.l字典文件名 = ( "用户攻击冷却时间.json", "反应戳一戳冷却时间.json", "彩蛋冷却时间.json")
        self.d用户攻击冷却时间, self.d反应戳一戳冷却时间, self.d彩蛋冷却时间 = self.获取.f获取字典数据(self.l字典文件名)
        self.l字典列表 = ( self.d用户攻击冷却时间, self.d反应戳一戳冷却时间, self.d彩蛋冷却时间 )

        logger.info('加载完成')

    @event_message_type(EventMessageType.GROUP_MESSAGE, priority=96)
    async def f主函数处理消息(self, event: AstrMessageEvent):

        v消息文本内容 = event.message_str

        if self.br开启百度百科 and v消息文本内容.startswith("百度百科") and len(v消息文本内容) > 4:
            event.stop_event(); v搜索词条 = v消息文本内容[4:].strip()
            if len(v搜索词条) > 30:
                yield event.plain_result("词条过长"); return
            if v搜索词条:
                百科结果 = await self.获取.f获取百科结果(v搜索词条); yield event.plain_result(百科结果)
            return

        if event.get_sender_id() in self.l黑名单用户: return  #在黑名单以下全部不响应

        v消息对象 = event.message_obj; 当前时间 = time.time()

        if event.message_obj.message and isinstance(event.message_obj.message[0], Poke):
            event.stop_event()
            async for i in f反应戳一戳(self, event, 当前时间): yield i

        if not v消息文本内容: return

        if any( i in v消息文本内容 for i in self.l关键词戳一戳 ):
            v发送者ID = v消息对象.sender.user_id; v群ID = v消息对象.group_id
            await f发送戳一戳(event, random.randint(1, self.v反戳次数), v群ID, v被戳者ID=v发送者ID)
            return

        # 戳一戳部分
        if not self.br戳一戳: return

        async for i in f戳一戳(self, event, v消息文本内容, v消息对象, 当前时间): yield i
        return

    #其他实现
    @filter.command("指令菜单")
    async def f指令菜单(self, event: AstrMessageEvent):
        event.stop_event()
        if not self.br指令菜单[0]: return
        if self.br指令菜单[1] and not event.is_admin(): return
        yield event.plain_result(self.v所有指令); return

    @filter.command("戳一戳次数")
    @filter.permission_type(filter.PermissionType.ADMIN, raise_error=False)
    async def f查看戳一戳次数(self, event: AstrMessageEvent):
        yield event.plain_result(f"今日戳一戳次数：{self.v今日戳一戳总次数}"); return

    async def terminate(self):
        """当插件被禁用、重载插件时会调用这个方法"""

        for 文件名, 字典 in zip(self.l字典文件名, self.l字典列表):
            保存路径 = os.path.join(self.v日志目录, 文件名)
            上级路径 = os.path.join(self.v上级目录, 文件名)
            try:
                with open(保存路径, 'w', encoding='utf-8') as f:
                    json.dump(字典, f, ensure_ascii=False, indent=2)
                shutil.copy(保存路径, 上级路径)
            except Exception as e:
                logger.error(f"保存{文件名}失败: {e}", exc_info=True)

        try:
            with open(self.v戳一戳日志文件名[0], 'w', encoding='utf-8') as f:
                文件内容 = f"当前日期：{date.today().strftime('%Y-%m-%d')}\n今日戳一戳总次数： {self.v今日戳一戳总次数}"
                f.write(文件内容)
            shutil.copy(*self.v戳一戳日志文件名)
            logger.info(文件内容)
        except Exception as e:
            logger.error(f"当前戳一戳总次数：{self.v今日戳一戳总次数}\n保存日志发送错误：\n{e}", exc_info=True)