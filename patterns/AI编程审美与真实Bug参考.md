# AI 编程代码审查审美：真实 Bug 参考

> 目标不是再加一份普通 checklist，而是训练一种“代码审美”：看到 AI 生成代码时，能判断它是稳、薄、虚、油滑，还是有真实工程质感。

## 一、核心判断

AI 编程带来的代码问题，很多不是“语法错”，而是**审美错**：

- 看起来完整，但没有边界。
- 看起来现代，但没有资源预算。
- 看起来抽象，但没有真实需求。
- 看起来自信，但没有证据链。
- 看起来可运行，但不尊重框架契约。

审查 AI 代码时，要把“能不能跑”降级为最低门槛，把注意力放到：**契约、边界、必要性、可恢复性、可验证性、局部修改的比例感**。

---

## 二、真实 Bug 与研究参考

### 2.1 LiteLLM 参数适配：契约错位

**真实参考**：

- [LiteLLM #11085: Claude Sonnet 4 does not support parameters: reasoning_effort](https://github.com/BerriAI/litellm/issues/11085)
- [LiteLLM #25321: streaming adapter drops tool_use input arguments](https://github.com/BerriAI/litellm/issues/25321)

**审美问题**：

适配层代码经常看起来只是“字段转换”，但它其实是系统边界。AI 很容易把 provider A 的参数、消息格式、tool schema、stream delta 结构，凭相似性套到 provider B。

**坏味道**：

```python
payload = {
    "model": model,
    "messages": messages,
    "reasoning_effort": "low",
    "tools": tools,
}

return client.chat.completions.create(**payload)
```

这段代码的表面问题是“可能有不支持参数”。更深的问题是：**没有 provider capability model**。代码不知道哪些模型支持哪些字段，只是把 OpenAI 风格的请求硬塞给所有后端。

**审美判断**：

差的适配层像“翻译腔”：字段名都在，但语义不在。

好的适配层应该像海关：

- 允许什么字段，有白名单。
- 丢弃什么字段，有日志。
- 转换什么字段，有测试。
- 不能转换时，失败要清晰。
- 流式工具调用要保留顺序和增量语义。

**审查问题**：

- [ ] 这段 adapter 是按 provider 显式建模，还是按字段名相似性猜？
- [ ] unsupported params 是静默丢弃、报错，还是有可观测降级？
- [ ] tool call 参数在 streaming 中是否会被截断、重排、合并丢失？
- [ ] 是否有跨 provider contract tests？

---

### 2.2 Copilot 生成代码安全弱点：流畅的不安全默认值

**真实参考**：

- [Security Weaknesses of Copilot-Generated Code in GitHub Projects](https://arxiv.org/abs/2310.02059)
- [Bugs in Large Language Models Generated Code: An Empirical Study](https://arxiv.org/abs/2403.08937)

研究里反复出现的模式包括：误解需求、缺少边界条件、错误输入类型、幻觉对象、错误属性、不完整生成，以及常见安全弱点。

**审美问题**：

AI 生成代码常常特别“顺”：变量名合理，函数短，调用链自然。但它倾向选择最常见写法，而最常见写法往往不是生产安全写法。

**坏味道：Python / Flask**

```python
query = f"SELECT * FROM users WHERE email = '{email}'"
rows = db.execute(query).fetchall()
```

**坏味道：Node.js**

```javascript
app.get("/profile", async (req, res) => {
  const user = await db.query(`select * from users where id = ${req.query.id}`);
  res.send(`<h1>${user.name}</h1>`);
});
```

**坏味道：Go**

```go
cmd := exec.Command("sh", "-c", "convert " + filename)
return cmd.Run()
```

**审美判断**：

不安全 AI 代码常有一种“教程感”：像博客第一屏示例，刚好省略了所有生产要害。

安全代码的审美不是啰嗦，而是**边界显性**：

- 输入是什么类型。
- 哪些值不可信。
- 哪些 API 必须参数化。
- 输出是否需要编码。
- 命令、路径、URL 是否有白名单。

**审查问题**：

- [ ] 这段代码是不是“教程级 happy path”？
- [ ] 用户输入进入 SQL、HTML、Shell、路径、URL、反序列化了吗？
- [ ] 安全动作是否依赖注释而不是 API 约束？
- [ ] 是否缺少最小权限、超时、限流、审计日志？

---

### 2.3 包名幻觉与 slopsquatting：依赖不是装饰品

**真实参考**：

- [We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs](https://arxiv.org/abs/2406.10279)
- [Snyk: Package hallucinations](https://snyk.io/articles/package-hallucinations/)
- [AI-Generated Code Is Not Reproducible Yet](https://arxiv.org/abs/2512.22387)

**审美问题**：

AI 很会写 `import`。它会生成看起来“像那个生态会存在”的包名。真正的问题不是安装失败，而是供应链攻击者可以把这个不存在的包名注册出来。

**坏味道：JavaScript**

```javascript
import { sanitizePaymentMemo } from "secure-payment-utils";
```

**坏味道：Python**

```python
from django_secure_fields import EncryptedJSONField
```

**坏味道：Rust**

```toml
[dependencies]
fast_jwt_validator = "1.2"
```

这些名字不一定存在，但都“像真的”。这就是 AI 依赖幻觉最危险的审美特征：**逼真但无出处**。

**审美判断**：

差的 AI 代码把依赖当作修辞：缺什么能力，就幻想一个库。

好的工程代码把依赖当作债务：

- 为什么引入。
- 谁维护。
- 下载量和 release 记录如何。
- license 是否可接受。
- lockfile 是否固定。
- 是否能用标准库或现有项目依赖完成。

**审查问题**：

- [ ] 新增包是否真实存在？
- [ ] 包名是否来自官方文档，而不是模型建议？
- [ ] 是否有 lockfile、hash、版本上限和安全扫描？
- [ ] 这个依赖是否只是为了省 20 行普通代码？

---

### 2.4 curl AI 漏洞报告：证据链比口气重要

**真实参考**：

- [Ars Technica: curl is sick of AI slop vulnerability reports](https://arstechnica.com/gadgets/2025/05/open-source-project-curl-is-sick-of-users-submitting-ai-slop-vulnerabilities/)
- [TechRadar: curl stops bug bounty over AI slop](https://www.techradar.com/pro/security/curl-will-stop-bug-bounties-program-due-to-avalanche-of-ai-slop)

这类材料不是“AI 写代码 bug”，但对代码审查审美很重要：AI 生成的漏洞报告可能有 CVSS、PoC、术语、严重性判断，却没有可复现证据。

**审美问题**：

AI 审查意见常有一种“安全报告腔”：

```text
This may lead to remote code execution under certain conditions.
The vulnerability has high impact due to improper bounds validation.
```

问题是：没有输入、没有路径、没有触发条件、没有栈、没有最小复现。

**审美判断**：

差的审查意见像判词，好的审查意见像实验记录。

好的 bug 报告至少要有：

- 受影响版本或 commit。
- 入口条件。
- 最小复现。
- 预期行为和实际行为。
- 为什么是安全问题，而不只是普通 bug。
- 修复方向与回归测试。

**审查问题**：

- [ ] 这条 AI 审查意见能不能复现？
- [ ] 是否引用了不存在的函数、版本、CVE 或 changelog？
- [ ] 严重性是否被证据支撑？
- [ ] 如果删掉形容词，剩下的事实还够吗？

---

### 2.5 Stack Overflow 对 AI 错误的讨论：幻觉不是随机噪音

**真实参考**：

- [Stack Overflow Blog: Detecting errors in AI-generated code](https://stackoverflow.blog/2024/09/20/detecting-errors-in-ai-generated-code/)

**审美问题**：

AI 错误不是完全随机的。它常沿着“最像答案的方向”犯错：

- API 名字像真的。
- 参数顺序像合理的。
- 错误处理像有了。
- 测试看起来覆盖了。
- 解释比代码更完整。

**审美判断**：

越像答案的代码，越要问它有没有证据。

**审查问题**：

- [ ] API 是否真的存在于当前版本？
- [ ] 测试是否真的会失败，而不是只验证 happy path？
- [ ] 解释是否反过来为代码找理由？
- [ ] 是否有“看起来合理但无人验证”的隐含前提？

---

## 三、跨语言审美雷达

### 3.1 Python：动态语言里的“温柔失败”

**AI 常见气质**：

- 字典随手取字段。
- `except Exception` 后返回默认值。
- 依赖 duck typing，但没有输入契约。
- 用字符串拼 SQL、Shell、路径。

**审美雷达**：

```python
def handle(payload):
    try:
        amount = float(payload["amount"])
        process(amount)
        return {"ok": True}
    except Exception:
        return {"ok": False}
```

这段代码不丑，但很软。它把所有错误磨成一个布尔值，审计线索消失。

**好品味**：

- Pydantic/dataclass 明确输入模型。
- 异常分类。
- 金额用 `Decimal`。
- 日志包含业务 id，不吞栈。
- 外部命令不用 shell 拼接。

---

### 3.2 JavaScript / TypeScript：类型的装饰化

**AI 常见气质**：

- TypeScript 写了类型，但 `as any` 把类型系统掏空。
- React 组件里堆状态、请求、权限、渲染。
- 前端隐藏按钮当作权限控制。
- `dangerouslySetInnerHTML` 没有清洗来源。

**审美雷达**：

```typescript
const user = response.data as any;
return <div dangerouslySetInnerHTML={{ __html: user.bio }} />;
```

这段代码有两个审美问题：类型是假的，HTML 信任也是假的。

**好品味**：

- `unknown` + schema parse。
- 权限在后端判定，前端只做展示。
- HTML 输出经过清洗。
- React 组件按数据、交互、展示拆分。

---

### 3.3 Go：错误处理被“整理”掉

**AI 常见气质**：

- 为了代码短，把错误合并或忽略。
- goroutine 没有 context。
- channel 没有关闭语义。
- defer 放在循环里造成资源延迟释放。

**审美雷达**：

```go
for _, url := range urls {
    go func() {
        resp, _ := http.Get(url)
        results <- resp.StatusCode
    }()
}
```

看起来并发，实际有闭包变量、错误丢失、无超时、无取消、无并发上限。

**好品味**：

- `context.Context` 从入口传到底。
- `errgroup.WithContext`。
- `SetLimit` 控制并发。
- 每个错误加上下文。
- 响应体及时关闭。

---

### 3.4 Rust：安全边界之外的自信

**AI 常见气质**：

- 以为 Rust 编译过就安全。
- 文件系统路径、权限、symlink、TOCTOU 没处理。
- `unwrap()` 出现在外部输入路径。
- 为了绕 borrow checker 过早引入 `Arc<Mutex<_>>`。

**审美雷达**：

```rust
let content = std::fs::read_to_string(path).unwrap();
let target = format!("{}/{}", base, user_input);
std::fs::write(target, content).unwrap();
```

Rust 的类型系统没有替你证明路径安全，也没有替你处理恶意文件名。

**好品味**：

- 外部输入不用 `unwrap/expect`。
- 路径 canonicalize 后检查边界。
- 创建文件用 `create_new` 等原子语义。
- 并发共享先问所有权模型，不急着上锁。

---

### 3.5 Swift：Optional 被“美化”成空值

**AI 常见气质**：

- 把 `nil` 改成 `""`、`[]`、默认对象。
- `Task {}` 隐式捕获 `self`。
- UI 更新没有 `@MainActor`。
- `async let` / `Task.detached` 用得像 JavaScript Promise。

**审美雷达**：

```swift
func displayName(_ user: User?) -> String {
    return user?.name ?? ""
}
```

这不是语法问题，而是契约问题：`nil` 可能代表“未登录”，空字符串代表“登录了但没名字”。AI 经常把语义差异擦平。

**好品味**：

- Optional 保留业务语义。
- UI 状态在 MainActor。
- 长生命周期 Task 明确取消。
- Delegate/closure 捕获关系清楚。

---

### 3.6 Java / Spring：框架契约被当注解装饰

**AI 常见气质**：

- `@Transactional` 到处贴。
- Controller 里写业务流程。
- `CompletableFuture.runAsync` 不传 executor。
- `@Async`、`@Scheduled`、连接池、事务传播互相不知道。

**审美雷达**：

```java
@Transactional
public void process(Order order) {
    repository.save(order);
    remoteClient.call(order);
    emailClient.send(order);
}
```

它看起来有事务，实际上把远程世界也幻想成本地事务的一部分。

**好品味**：

- 注解背后的代理机制要说得清。
- 事务边界短。
- 外部副作用 after commit / outbox。
- 阻塞任务使用隔离线程池。
- 幂等靠数据库约束兜底。

---

## 四、AI 代码审查审美词典

### 4.1 “薄”

代码只有 happy path，缺少边界、异常、日志、回滚、限流。

**典型句式**：

> 这段代码的主路径很顺，但厚度不够。请补齐失败路径、资源边界和可观测性。

### 4.2 “油”

抽象很多，命名很漂亮，但没有真实复杂度支撑。

**典型句式**：

> 这里的 pattern 比问题本身重。先用直接函数表达业务规则，等出现第二个变化点再抽象。

### 4.3 “虚”

解释比代码可靠，事实链断裂。

**典型句式**：

> 这条结论需要源码、文档或测试证明。现在只是模型对 API 行为的猜测。

### 4.4 “硬”

类型、约束、边界、状态机都写进代码和数据库，不靠口头约定。

**典型句式**：

> 这个约束应该下沉到类型或数据库唯一索引，而不是只放在 if 判断里。

### 4.5 “稳”

失败可恢复，重试幂等，资源有上限，日志能定位。

**典型句式**：

> 这段逻辑不仅要成功，还要能解释失败、恢复失败、限制失败的范围。

---

## 五、真实 Bug 驱动的审查动作

### 动作 1：向代码要证据

适用：AI 解释 API 行为、框架行为、性能收益。

```text
请指出这个行为来自哪份官方文档、哪个源码分支或哪条测试。
```

### 动作 2：检查“相似 API 误用”

适用：跨 provider、跨云厂商、跨数据库、跨语言迁移。

```text
这个字段在目标后端是否支持？同名字段的语义是否一致？
```

### 动作 3：从异常路径读设计

适用：支付、任务、消息、文件、网络。

```text
如果第 N 步成功、第 N+1 步失败，系统处于什么状态？
```

### 动作 4：把新增依赖当 PR 主角

适用：AI 新增 import/package。

```text
这个包是否真实、必要、可信？是否有 lockfile 和安全扫描？
```

### 动作 5：看抽象有没有“第二个调用者”

适用：AI 过度设计。

```text
这个接口、工厂、适配器、策略对象，服务的变化点是什么？现在有没有第二个实现？
```

---

## 六、AI 代码审查高价值问题清单

```
□ 这段代码是否只证明了 happy path？
□ 这段代码的边界是类型保证、数据库保证，还是注释保证？
□ 新增依赖是否真实存在并值得引入？
□ AI 是否把一个生态的 API 套到了另一个生态？
□ 失败后是否可重试、可恢复、可定位？
□ 并发、连接、内存、队列是否有预算？
□ 安全动作是否使用安全 API，而不是手写字符串处理？
□ Optional/null/空字符串是否被混为一谈？
□ 错误是否被“整理”成无信息的 false/null/默认值？
□ 抽象是否服务真实变化点？
□ 测试是否覆盖会失败的路径？
□ 审查意见是否能复现，还是只有严重性形容词？
```

---

## 七、一句话总结

AI 代码的审美训练，本质是练习不被“像样”迷惑。真正好的代码不只是会表达成功路径，它还知道自己和世界的边界在哪里。
