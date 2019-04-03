# Scrapy-Redis-Zhihu
## 如何使用
### 安装依赖
```
git clone https://github.com/Yanxueshan/Scrapy-Redis-Zhihu.git
cd Scrapy-Redis-Zhihu
pip install -r requirements.txt
```

### 参数修改
settings.py中的某些参数需要修改
```
#　这是数据库ＭｙＳＱＬ相关配置，修改为自己的ＭｙＳＱＬ配置
MYSQL_HOST = 'localhost'
MYSQL_DBNAME = 'zhihu'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'

# 这是知乎的账号和密码，供模拟登录使用，修改为自己的知乎账号和密码
ZHIHU_ACCOUNT = 'username'
ZHIHU_PASSWORD = 'password'

# 这是超级鹰的账号，用来识别英文验证码，修改为自己的超级鹰账号（也可以换成其他第三方平台，不过相应的zhihu.py中的代码要改变）
CHAOJIYING_ACCOUNT = 'username'
CHAOJIYING_PASSWORD = 'password'
CAPTCHA_TYPE = '898966'
```

### 运行前准备
开启redis-server和redis-cli
```
# 切换到redis安装目录下
cd redis
redis-server.exe redis.windows.conf

# 另起一个窗口
redis-cli
```
