# python网络流实战
## 任务要求
实现类net assist的功能，支持udp和tcp以及文件传输
官方doc不好看，还是用底层api吧
### 样例
input("请输入你的协议类型: UDP/TCPS/TCPC")
需要支持udp和tcp(server and client)

在接受到协议后，如果是TCPS需要准备接受host和port作为本地addr
TCPC则需两遍接受作为本地和远端

input(">")
表示准备接受发送的数据
UDP第一次发送数据前需要命令`BIND 127.0.0.1 8888`作为目标地址,其后再次使用BIND换绑
TCPS每次发送信息时会显示已经建立连接的客户端，需要手动选择接收目标。
`MSG hello world`发送信息样例
`FILE D:/no.txt`绝对地址,`FILE /hi.txt`相对地址。

接受信息，
接受到信息时，直接显示在命令行中`hello FROM 127.0.0.1:8888`
文件自动保存在当前目录，名称为发送文件的名称，并显示在命令行中`NEW FILE FROM 127.0.0.1:8888`。

`CLOSE` 关闭当前连接。
`EXIT`退出整个程序

## 特别提醒
由于设计的缺失，所有的任务没有分散给各个模块，如mydata.py承担了所有的文件传输功能并且发送和接受都在一个类中。
另外，博主不会做到忽略一个input，因此在确定是否接受文件时需要先输入一个回车来忽略先前异步的ainput