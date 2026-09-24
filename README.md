# RentFind 租房与物业报修平台

```bash
cp .env.example .env
docker compose up -d --build
```

RentFind 面向房东、租客和物业人员，提供房源发布、搜索预约、合同管理和报修跟踪能力。

## 项目主要功能

- 房源发布：小区、户型、面积、租金、押金、付款方式、照片和设施。
- 搜索筛选：区域、价格、户型、面积、设施，并支持列表和地图视图切换。
- 预约看房：租客选择时间段，房东确认后生成通知。
- 合同管理：生成租赁合同模板并记录租期、租金、双方信息和状态。
- 合同续租：租客从合同卡片发起续租（新租期 + 期望月租）；房东接受、还价或拒绝，还价后由租客确认；新租期与同一房源其他有效合同重叠时给出冲突说明；成功后自动生成下一份合同，原合同标记为已续租且不再更改；卡片状态为待房东处理 / 待租客确认 / 已续租 / 已取消，每次处理都留下角色和时间。
- 物业报修：提交故障类型、描述和照片，物业接单并更新进度。
- 角色区分：房东、租客、物业人员拥有不同工作台。

## 快速启动方式

首次启动前执行：

```bash
cp .env.example .env
docker compose up -d --build
```

访问地址：http://localhost:18407

## 本地开发方式

```bash
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python manage.py runserver 0.0.0.0:8000
cd frontend && npm install && npm run dev
```

## 续租协商说明

为避免续租约定散落在聊天里、同一套房被口头答应给两个人，续租在合同卡片内闭环：

- 租客填写**新租期**和**期望月租**发起续租，卡片进入「待房东处理」。
- 房东可**接受**（直接续租成功）、**还价**（改价后卡片转为「待租客确认」）或**拒绝」（已取消）。
- 还价后由租客**确认**或**取消续租**；房东接受与租客确认时都会校验新租期是否与**同一房源的其他有效合同**重叠，重叠则返回 409 并列出冲突合同（租客、租期、租金），协商状态不变。
- 续租成功后原子生成**下一份合同**，原合同变为「已续租」并指向新合同，不能再次更改或续租。
- 每次处理都会写入处理流水（角色、姓名、动作、时间），卡片可展开查看。
- 卡片四种状态：待房东处理、待租客确认、已续租、已取消。

接口（演示身份通过 `X-User-Role: tenant|landlord` 与 `X-User-Name`（百分号编码）请求头传入）：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/contracts/` | 当前角色的合同卡片（含最近一次续租协商） |
| POST | `/api/renewals/` | 租客发起续租 |
| POST | `/api/renewals/{id}/accept/` | 房东接受 |
| POST | `/api/renewals/{id}/counter/` | 房东还价（body：`proposedRent`） |
| POST | `/api/renewals/{id}/reject/` | 房东拒绝 |
| POST | `/api/renewals/{id}/confirm/` | 租客确认还价 |
| POST | `/api/renewals/{id}/cancel/` | 租客取消 |

后端首次迁移会写入演示数据：房东「宋房东」、租客「陈晨」；海棠公寓在 `2026-10-01 ~ 2027-09-30` 已存在另一位租客「林悦」的有效合同，可用来演示租期冲突。

## 技术栈| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Element Plus、Vite、高德地图 JS API |
| 后端 | Python、Django、Django REST Framework |
| 数据库 | PostgreSQL |
| 认证 | JWT |
| 部署 | Docker Compose、Nginx |

## 项目目录结构

```text
.
├── backend
│   ├── app
│   ├── database
│   └── manage.py
├── frontend
│   ├── src
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## 环境变量说明

| 变量 | 说明 |
| --- | --- |
| COMPOSE_PROJECT_NAME | Compose 项目名，固定为 rentfind |
| DATABASE_URL | Django 连接 PostgreSQL 的地址 |
| DJANGO_SECRET_KEY | Django 密钥 |
| AMAP_KEY | 高德地图 JS API Key |

## Docker 部署说明

Compose 顶层声明 `name: rentfind`，容器名带 `rentfind-` 前缀，数据库和媒体文件分别使用命名卷持久化，前端 Nginx 将 `/api` 代理到后端 `backend:8000`。

## License

MIT
