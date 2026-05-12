# 代码审查模式库

> 积累各类语言的代码审查checklist和反模式

---

## 一、AI生成代码审查模式

### 1.1 必查项

| 检查项 | 描述 | 风险等级 |
|--------|------|----------|
| **输入验证** | 是否信任用户输入？是否有SQL/命令注入风险？ | 🔴 高 |
| **边界条件** | 空值、0、空串、极大值是否处理？ | 🔴 高 |
| **硬编码** | API密钥、凭证、魔法数字？ | 🔴 高 |
| **依赖安全** | 建议的包是否可信？版本是否过时？ | 🟡 中 |
| **复杂度** | 是否为通过测试牺牲可读性？ | 🟡 中 |
| **并发安全** | 多线程/并发场景是否有竞态条件？ | 🔴 高 |

### 1.2 AI常见Bug模式

```
1. 假的安全感：代码能跑，但有隐藏漏洞
2. 过度简化：用一行复杂表达式替代多行清晰代码
3. 边界忽略：相信Happy Path，忽略异常路径
4. 版本幻觉：使用不存在的API或已废弃的特性
5. 上下文丢失：忽略项目已有的代码风格和约定
```

### 1.3 反向审查问句

> 假设这是AI生成的，它最可能隐瞒的3个弱点是什么？

---

## 二、并发编程审查模式

### 2.1 Go并发审查

```go
// ✅ Good: 使用Channel传递数据
ch := make(chan Result)
go func() { ch <- fetch() }()
result := <-ch

// ❌ Bad: 共享内存+Mutex
var mu sync.Mutex
var data string
mu.Lock()
data = "shared"
mu.Unlock()
```

**审查要点**:
- Channel是否正确关闭？
- 是否有goroutine泄露？
- 是否有死锁风险？

### 2.2 Rust并发审查

```rust
// ✅ Good: Arc<Mutex<T>> 或 Arc<RwLock<T>>
let counter = Arc::new(Mutex::new(0));
let c = counter.clone();
tokio::spawn(async move {
    *c.lock().await += 1;
});

// ❌ Bad: 跨线程传递非Send类型
```

**审查要点**:
- 类型是否实现Send/Sync trait？
- 生命周期是否正确？
- 是否有数据竞争？

### 2.3 并发反模式

| 反模式 | 描述 | 修复方案 |
|--------|------|----------|
| **锁粒度过粗** | 全局锁导致并发退化 | 缩小锁范围 |
| **忘记释放锁** | Lock后无Unlock | defer / RAII |
| **死锁** | 循环等待 | 固定锁顺序 |
| **goroutine泄露** | 协程未结束 | context取消 |

---

## 三、泛型设计审查模式

### 3.1 TypeScript泛型

```typescript
// ✅ Good: 约束充分
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}

// ❌ Bad: 无约束，返回any
function getProperty(obj: any, key: string): any {
    return obj[key];
}
```

**审查要点**:
- 泛型约束是否充分？
- 是否需要多重约束？
- 默认类型参数是否合理？

### 3.2 泛型反模式

| 反模式 | 描述 | 修复方案 |
|--------|------|----------|
| **any滥用** | 放弃类型安全 | 使用泛型约束 |
| **约束缺失** | T无限制 | `<T extends SomeType>` |
| **over-engineering** | 简单场景用复杂泛型 | YAGNI原则 |

---

## 四、资源管理审查模式

### 4.1 Rust RAII

```rust
// ✅ Good: Drop trait自动释放
struct File { file: std::fs::File }
impl Drop for File {
    fn drop(&mut self) { /* 清理 */ }
}

// ❌ Bad: 手动管理，易出错
fn bad() {
    let file = open();
    if condition { return; } // 泄漏！
    close(file);
}
```

### 4.2 Go defer

```go
// ✅ Good: defer确保释放
func good() {
    file, _ := os.Open("file.txt")
    defer file.Close()
    // ... 使用file
}

// ❌ Bad: 多个defer执行顺序错误
func bad() {
    defer cleanup1() // 后进先出
    defer cleanup2()
}
```

### 4.3 资源管理反模式

| 反模式 | 描述 | 修复方案 |
|--------|------|----------|
| **忘记释放** | 路径分支多易遗漏 | defer/RAII |
| **defer在循环内** | 性能问题 | 移到循环外 |
| **defer掩盖错误** | defer中panic | 检查recover |

---

## 五、持续更新

- **Day 1**: 函数式编程反模式、Swift错误处理模式
- **Day 2**: AI生成代码Bug分类、Rust vs Go并发对比、TS泛型设计
- **Day 3**: 待补充...
