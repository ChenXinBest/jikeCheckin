# jikeCheckin
极客云签到，顺便测试work flow
# 使用方法
使用方法
Github Actions版本
1. 点击项目右上角的Fork，Fork此项目
2. 到自己Fork的项目点击Setting→Secrets→New secrets
3. Name填写jike_email，Value填写极客网的邮箱地址；
4. 另外再新建一个secrets，分别填上jike_password以及极客网的密码
4.在"Actions"中的"run"下点击"Run workflow"即可手动执行签到，后续运行按照schedule，默认在每天凌晨00:30自动签到，可自行修改