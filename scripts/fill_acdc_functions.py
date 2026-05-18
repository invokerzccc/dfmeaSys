"""为 ACDC模块-24V (node_id=30) 创建功能分析"""
import requests

BASE = "http://localhost:8000/api/v1"
NODE_ID = 30

functions = [
    {
        "function_desc": "AC-DC电源变换与稳压输出",
        "requirement": "将来自柜内380VAC母线（两相）的交流电压转换为稳定的24VDC输出，为后级板卡负载（MCU、通讯模块、传感器供电）及底板上其他功率元件提供额定20A/480W的直流电源。额定输入200~480VAC，支持宽范围180~600VAC输入以适应现场电网波动。输出电压支持24~28V可调，满足不同距离线缆压降补偿需求。满载效率≥93%(400VAC)，降低柜内热耗散。",
        "performance_spec": "额定输入电压：200~480VAC（认证电压）\n输入电压范围：180~600VAC / 250~850VDC\n输入频率：47~63Hz\n额定输出：24VDC/20A（480W）\n输出电压可调范围：24~28VDC\n输出电压精度：±1%（全负载范围）\n线性调节率：±0.5%\n负载调节率：±1%（0-100%负载）\n效率：93%（400VAC满载，Typ）\n输出纹波噪声：≤100mVpp（20MHz带宽，峰-峰值）\n最大容性负载：20000μF\n温度漂移系数：±0.03%/℃（0~50℃）\n待机功耗：≤4W（400VAC）\n最小负载：0%（空载可正常工作）",
    },
    {
        "function_desc": "主动功率因数校正(PFC)",
        "requirement": "内置主动式PFC电路，降低输入电流谐波含量，提高功率因数至≥0.93（230VAC）。满足IEC/EN 61000-3-2谐波电流Class A限值要求，减少对上游配电系统（变压器、ATS切换柜）的无功电流冲击和谐波污染，避免引起同柜其他ACDC模块的输入电流振荡。",
        "performance_spec": "功率因数：≥0.93（230VAC满载，Typ：0.95）\n功率因数：≥0.92（400VAC满载，Typ：0.94）\n谐波电流：满足IEC/EN 61000-3-2 Class A\n输入电流：≤4A（230VAC）/ ≤1.6A（400VAC）\n冲击电流：≤30A（400VAC冷启动）\n启动延迟时间：≤0.8s",
    },
    {
        "function_desc": "输出过流/短路保护",
        "requirement": "输出端发生过流（≥130%额定电流）或直接短路时，自动进入恒流-打嗝保护模式，防止功率器件过热损坏、PCB走线熔断及火灾风险。故障消除后自动恢复正常输出，无需人工干预。支持长期短路不损坏。液冷机组现场安装/维护期间可能存在输出接线意外短路，模块需可靠保护。",
        "performance_spec": "过流保护触发：≥130%Io（≥26A）\n过流保护模式：恒流模式3s(Typ)后进入打嗝模式（自动恢复）\n短路保护模式：恒流3s(Typ)后打嗝，可长期短路不损坏，自恢复\n150%Io峰值电流：可持续3s（用于电机/容性负载启动）\n保护响应时间：由内部ASIC/PWM控制器硬件实现，μs级",
    },
    {
        "function_desc": "输出过压保护",
        "requirement": "ACDC内部反馈环路或功率级故障导致输出电压异常升高时，触发过压保护，进入打嗝模式，防止后级板卡（MCU、通讯芯片）及传感器因过压烧毁。过压阈值低于后级输入保护电路（过压防护: 33V关断）的响应范围，形成分级保护。",
        "performance_spec": "过压保护阈值：≤33VDC（24V型号）\n保护模式：打嗝式，故障消除后自恢复\n与后级过压保护的分级协调：ACDC OVP ≤33V → 后级过压关断35V±1V（硬件钳位≥40V）",
    },
    {
        "function_desc": "过温保护",
        "requirement": "当模块内部温度因通风不良、风扇故障或长期过载运行而超过安全上限时，自动降低输出功率或关断输出，防止功率器件（开关管、整流管）热击穿、电解电容加速老化及PCB碳化。温度恢复正常后自动恢复。液冷机组柜内因冷却系统故障可能导致环境温度急剧升高。",
        "performance_spec": "过温保护触发温度：≤80℃（额定负载，内部测温点）\n过温保护释放温度：≥55℃\n工作温度范围：-40~+85℃\n满载工作温度：最高50℃（无需降额）\n温度降额：+50~+70℃: 2.0%/℃；+70~+85℃: 3.33%/℃\n冷却方式：自然空冷（无风扇设计）",
    },
    {
        "function_desc": "DCOK输出状态信号",
        "requirement": "提供DCOK（直流输出正常）隔离信号输出，用于MCU采集模块的输出电压状态。当24V输出电压在正常范围内时，DCOK为有效状态；当输出欠压、过压保护动作或模块关机时，DCOK状态翻转。MCU据此判断电源是否正常工作，用于系统级故障诊断和保护联锁逻辑。",
        "performance_spec": "DCOK隔离电压：≥500VAC（输出-DCOK，1分钟，漏电流＜1mA）\nDCOK EFT抗扰度：±1KV（IEC/EN 61000-4-4）Perf. Criteria A\nDCOK浪涌抗扰度：±1KV（DCOK to PE，IEC/EN 61000-4-5）Perf. Criteria A\nDCOK响应时间：由内部检测电路决定（≤ms级）",
    },
    {
        "function_desc": "150%峰值功率输出",
        "requirement": "支持在额定功率基础上提供150%（30A/720W）的峰值功率输出，持续3秒。用于启动直流电机（如小型冷却泵）、容性负载充电及其他瞬态重负载场景，避免因启动电流瞬增触发ACDC过流保护导致系统无法正常启动。",
        "performance_spec": "峰值功率：150%Io（30A）\n持续时间：3s（Typ）\n触发条件：400VAC输入，负载需求超过额定值\n恢复：峰值结束后自动返回额定输出模式",
    },
    {
        "function_desc": "输入输出安全隔离",
        "requirement": "在380VAC高压输入端与24VDC低压输出端之间提供≥4000VAC的电气隔离，满足安全特低电压（SELV）要求，保护操作人员和后端低压电路免遭高压触电危险。符合EN 62368-1 / UL 61010-1安全标准。同时隔离输入端的对地故障和浪涌残余，防止传递至低压侧。",
        "performance_spec": "输入-输出隔离电压：4000VAC（1分钟，漏电流＜5mA）\n输入-地隔离电压：2000VAC（1分钟，漏电流＜5mA）\n输出-地隔离电压：500VAC（1分钟，漏电流＜5mA）\n绝缘电阻：≥100MΩ（500VDC测试电压，各端口对）\n安全等级：CLASS I（需保护接地）\n过电压等级：Ⅲ（2000m，参考EN 61010）\n海拔适用：5000m（2000m以上温度降额3.5℃/km）",
    },
    {
        "function_desc": "EMC电磁兼容性",
        "requirement": "模块自身满足工业环境EMC发射和抗扰度标准要求，不对同柜内其他设备（MCU、传感器、通讯模块）产生电磁干扰，也能耐受外部电磁骚扰（变频器谐波、接触器电弧、对讲机辐射）不出现功能降级或损坏。EMC测试需结合终端设备（液冷机组）整体确认。",
        "performance_spec": "EMI 传导骚扰：CISPR32/EN55032 Class B\nEMI 辐射骚扰：CISPR32/EN55032 Class B\nEMS 静电放电(ESD)：IEC 61000-4-2 ±8kV接触/±15kV空气，Criteria A\nEMS 辐射抗扰度：IEC 61000-4-3 10V/m，Criteria A\nEMS 脉冲群(输入端)：IEC 61000-4-4 ±4KV，Criteria A\nEMS 脉冲群(输出端)：IEC 61000-4-4 ±2KV，Criteria A\nEMS 浪涌(输入端)：IEC 61000-4-5 线-线±2KV/线-PE±4KV，Criteria A\nEMS 浪涌(输出端)：IEC 61000-4-5 Vo+toVo-±500V / toPE±1KV，Criteria A\nEMS 传导抗扰度：IEC 61000-4-6 10Vrms，Criteria A\nEMS 工频磁场：IEC 61000-4-8 30A/m，Criteria A\nEMS 电压暂降/跌落/中断：IEC 61000-4-11，Criteria B\n电压闪烁：IEC 61000-3-3，满足",
    },
    {
        "function_desc": "输入电压暂降耐受",
        "requirement": "电网电压发生短时暂降、跌落或中断时，利用内部储能电容维持输出至少20ms（400VAC满载），确保MCU和控制电路在电网异常期间继续工作并完成数据保存和状态记录，避免系统异常复位。液冷机组现场电网可能因大功率设备（压缩机、加热器）启停而出现电压暂降。",
        "performance_spec": "掉电保持时间：≥20ms（400VAC/500VAC满载）\n电压暂降耐受：IEC 61000-4-11 100%dip 1周期/30%dip 25周期（50Hz），Criteria B\n内置储能：输入电解电容组（通过PFC升压后母线电容）",
    },
]

for i, func in enumerate(functions):
    resp = requests.post(f"{BASE}/nodes/{NODE_ID}/functions", json=func)
    if resp.status_code == 201:
        data = resp.json()
        print(f"[{i+1}/{len(functions)}] OK: id={data['id']} {data['function_desc']}")
    else:
        print(f"[{i+1}/{len(functions)}] FAIL: {resp.status_code} {resp.text}")
