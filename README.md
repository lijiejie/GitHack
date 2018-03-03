# GitHack


GitHack is a `.git` folder disclosure exploit. 

It rebuild source code from .git folder while keep directory structure unchanged.

GitHack是一个.git泄露利用脚本，通过泄露的.git文件夹下的文件，重建还原工程源代码。

渗透测试人员、攻击者，可以进一步审计代码，挖掘：文件上传，SQL注射等web安全漏洞。

## 工作原理 ##

* 解析.git/index文件，找到工程中所有的： ( 文件名，文件sha1 )
* 去.git/objects/ 文件夹下下载对应的文件
* zlib解压文件，按原始的目录结构写入源代码

## 用法示例 ##
    GitHack.py http://www.openssl.org/.git/

## Thanks ##
Thanks for sbp's great work, I used his .git index parser [gin - a Git index file parser](https://github.com/sbp/gin).

