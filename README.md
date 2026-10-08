# 吉隆口岸泥石流监测救援部署系统

本项目用于苍穹杯空间信息技术大赛，采用 Vue 3、OpenLayers、Django 5 和 KQGIS Server，展示吉隆口岸影像、吉隆县专题图、管理员点位派遣及救援组长任务上报闭环。

## 快速入口

- Windows 一键启动：双击根目录的 `一键启动全部环境.cmd`
- 启动全部本地服务：`powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`
- 执行代码检查：`powershell -ExecutionPolicy Bypass -File .\scripts\verify-project.ps1`
- 管理员端：[http://127.0.0.1:5173/#/login](http://127.0.0.1:5173/#/login)
- 组长任务端：[http://127.0.0.1:5174/](http://127.0.0.1:5174/)
- 局域网与公网访问配置：[docs/NETWORK_ACCESS.md](docs/NETWORK_ACCESS.md)
- 查看完整目录说明：[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- 查看应用开发说明：[app/README.md](app/README.md)
- 查看 KQGIS 服务说明：[docs/KQGIS_基础地图服务说明.md](docs/KQGIS_基础地图服务说明.md)

## 重要约束

- `尼泊尔泥石流巨灾` 是原始赛事数据，不在应用运行时修改。
- `Gis` 同时包含 KQGIS 程序和运行数据，已发布服务依赖现有绝对路径，不应随意移动或改名。
- `kqgis_publish` 保存地图工程和发布验收图，不是前端静态资源。
- 页面数据必须来自原始文件、数据库中的管理员操作或手机端实际上报，不使用原型图中的示意数字。
- 两个前端默认监听全部网卡；Django 与 KQGIS 仍保持本机监听并通过前端代理访问。正式公网部署前必须更换密钥、关闭调试模式并启用 HTTPS。

## GitHub 公开副本

此仓库不含 KQGIS 程序、许可证、运行数据库、原始影像和大视频，下载后需要准备外部数据和 GIS 环境。参见 [GitHub公开版说明.md](GitHub公开版说明.md) 与原始数据目录中的文件清单。
