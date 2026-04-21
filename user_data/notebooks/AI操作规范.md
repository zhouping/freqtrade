
#严重警告！严禁使用 "现货模式+期货数据" 方式进行回测和hyperopt操作！！！

Freqtrade 项目的目录及操作规范：

• 项目根目录：/home/kali/Project/freqtrade/
• 用户数据根目录：/home/kali/Project/freqtrade/user_data/
子目录：
  • notebooks/ — 研究文档
  • scripts/ — 自编代码/脚本
  • data/ — K线历史数据
  • logs/ — 日志/报错
  • backtest_results/ — 策略回测结果

注意：
0、不要随意修改 freqtrade 项目源代码，除非得到批准。不要随意在 /home/kali/Project/freqtrade/user_data/ 目录之外随意修改/添加文件/代码/脚本。
1、自编代码存 scripts，历史K线数据存 data目录，操作日志/报错信息存 logs目录
2、策略回测/优化操作的结果保存在backtest_results目录，保存方式必须遵循 notebooks/回测结果保存说明.md 中的规定
3、回测/优化遇到问题，查看 '策略测试相关问题.md' 中是否有解决办法
4、必须使用 freqtrade 进行回测/优化等操作，严禁编写什么standalone 脚本绕过 freqtrade !!!

