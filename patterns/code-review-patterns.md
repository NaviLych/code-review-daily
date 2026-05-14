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

### 2.4 Java v22+ 并发审查（AI生成代码重灾区）

#### Collections选择决策表

| 场景 | ❌ AI常生成的错误选择 | ✅ 正确选择 |
|------|---------------------|-------------|
| 复合操作（遍历+删除） | `Collections.synchronizedList()` | `ConcurrentLinkedQueue` |
| 读多写少+需索引 | `synchronizedList()` | `CopyOnWriteArrayList` |
| 高并发Map | `Hashtable` | `ConcurrentHashMap` |
| 需要阻塞取元素 | `List + wait/notify` | `BlockingQueue` |

#### Virtual Threads 雷区

```java
// ❌ 致命错误: synchronized阻塞carrier线程
public class BadService {
    public synchronized void doSomething() { /* ... */ }
}

// ✅ 正确做法: ReentrantLock + tryLock超时
public class GoodService {
    private final ReentrantLock lock = new ReentrantLock();
    public void doSomething() throws InterruptedException {
        if (lock.tryLock(5, TimeUnit.SECONDS)) {
            try { /* ... */ }
            finally { lock.unlock(); }
        }
    }
}
```

#### StructuredTaskScope 生命周期的关键

```java
// ❌ AI常漏掉join - 导致Virtual Thread泄漏
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    scope.fork(() -> task());
    // 缺少 scope.join() 和 scope.throwIfFailed()
}

// ✅ 完整模式
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    List<Subtask<T>> tasks = items.stream()
        .map(item -> scope.fork(() -> process(item)))
        .toList();
    scope.join();           // 必须等待完成
    scope.throwIfFailed();  // 必须传播异常
    return tasks.stream().map(Subtask::get).toList();
}
```

#### CompletableFuture 异常处理模板

```java
// ❌ AI常省略异常处理 - 错误静默消失
.thenApply(user -> generateReport(user));

// ✅ 必须添加异常处理
.thenApply(user -> generateReport(user))
.whenComplete((result, ex) -> {     // 日志记录
    if (ex != null) log.error("Failed", ex);
})
.handle((result, ex) -> {           // 恢复或返回错误
    if (ex != null) return "Error: " + ex.getMessage();
    return result;
});
```

#### 懒初始化的正确姿势

```java
// ❌ Double-checked locking: 过度复杂
private volatile Connection conn;
if (conn == null) {
    synchronized (this) {
        if (conn == null) conn = create();
    }
}

// ✅ Holder模式: 让JVM处理线程安全
private static class Holder {
    static final Connection INSTANCE = createConnection();
}
public Connection get() { return Holder.INSTANCE; }
```

#### AI生成Java并发代码必查清单

- [ ] 是否使用`Collections.synchronized*()`？检查复合操作
- [ ] 是否在Virtual Threads场景使用`synchronized`？
- [ ] `CompletableFuture`链是否有`whenComplete`/`handle`？
- [ ] `StructuredTaskScope`是否调用了`scope.join()`？
- [ ] 懒初始化是否需要？考虑Holder模式替代DCL

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
- **Day 4**: Rust TOCTOU/Ghost Bits/Swift并发陷阱（来源：uutils审计44 CVE）

---

## 六、Rust系统编程审查模式（2026-05-14新增）

### 6.1 TOCTOU竞态条件

> **核心原则：同一路径执行两次操作时，假设存在TOCTOU Bug直到被证明安全**

```rust
// ❌ 危险：两次syscall之间可被攻击
fs::remove_file(to)?;              // 第1次：检查
// ← 攻击者可在此植入symlink
let mut dest = File::create(to)?; // 第2次：跟随symlink！
copy(from, &mut dest)?;

// ✅ 安全：使用create_new防止symlink
let mut dest = OpenOptions::new()
    .write(true)
    .create_new(true)  // O_EXCL：不存在则失败
    .open(to)?;
```

**审查要点**：
- [ ] 代码是否对同一路径执行两个操作？
- [ ] 两个操作之间文件系统状态是否可变？
- [ ] 第二个操作是否会跟随symlink？
- [ ] 是否可以使用文件描述符替代路径名？

### 6.2 类型边界检查

> **核心原则：char/Unicode到字节的转换要格外小心**

```rust
// ❌ 危险：char截断，WAF绕过攻击
#[allow(trivial_casts)]  // 需要显式忽略警告！
for ch in s.chars() {
    bytes.push(ch as u8);  // ħ (U+0127) → 0x27 = '\''
}

// ✅ 安全：使用bytes()迭代器
for b in s.bytes() {  // b已经是u8，无需转换
    bytes.push(b);
}

// ✅ 安全：输入验证
fn is_valid_ascii(s: &str) -> bool {
    s.chars().all(|ch| ch.is_ascii())
}
```

**审查要点**：
- [ ] 是否有`#[allow(trivial_casts)]`？
- [ ] 是否有输入验证（ASCII范围）？
- [ ] 是否可以使用`bytes()`迭代器替代？

### 6.3 权限设置时序

> **核心原则：权限应在创建时设置，而不是之后修改**

```rust
// ❌ 危险：创建后设置，存在暴露窗口
fs::create_dir(&path)?;
fs::set_permissions(&path, Permissions::from_mode(0o700))?;
// ← 其他用户此时可以访问！

// ✅ 安全：创建时设置
fs::create_dir(&path)?
    .with_permissions(Permissions::from_mode(0o700));
// 或使用OpenOptions::mode()
```

### 6.4 路径比较安全

> **核心原则：字符串比较不可靠，必须先规范化**

```rust
// ❌ 危险：可被/../绕过
if file == Path::new("/") { ... }

// ✅ 安全：规范化后再比较
fn is_root(file: &Path) -> bool {
    matches!(fs::canonicalize(file), Ok(p) if p == Path::new("/"))
}
```

### 6.5 panic即DoS

> **核心原则：外部输入导致的unwrap/expect是DoS漏洞**

```rust
// ❌ 危险：攻击者可导致panic
let path = std::str::from_utf8(bytes)
    .expect("Could not parse...");  // 非UTF-8文件名 → 崩溃

// ✅ 安全：优雅错误处理
match std::str::from_utf8(bytes) {
    Ok(s) => process(s),
    Err(e) => return Err(ParseError::InvalidUtf8(e)),
}
```

### 6.6 信任边界跨越

> **核心原则：跨越信任边界前完成所有解析**

```rust
// ❌ 危险：chroot后加载用户信息
chroot(new_root)?;                  // 进入攻击者文件系统
let user = get_user_by_name(name)?; // 加载攻击者的.so！

// ✅ 安全：跨越前解析
let user = get_user_by_name(name)?;  // 在安全侧解析
chroot(new_root)?;
```

### 6.7 Rust审查checklist

- [ ] **TOCTOU检查**：同一路径是否执行两次操作？
- [ ] **权限时序**：权限是否在创建时设置？
- [ ] **路径比较**：是否使用`canonicalize`？
- [ ] **panic风险**：是否有`unwrap`/`expect`处理外部输入？
- [ ] **字节流处理**：是否使用`OsStr`/`&[u8]`？
- [ ] **allow属性**：`#[allow(...)]`是否经过审视？
- [ ] **信任边界**：跨越边界前是否完成所有解析？

---

## 七、Swift并发审查模式（2026-05-14新增）

### 7.1 asyncLet任务管理

> **核心原则：asyncLet变量必须在作用域内正确await**

```swift
// ❌ 危险：asyncLet任务完成竞态
async let task1 = HTTPSCallable.call()
async let task2 = anotherCall()
// 等待时序问题可能导致 swift_Concurrency_fatalError

// ✅ 安全：确保任务正确await
let (r1, r2) = await (task1, task2)
```

### 7.2 Actor Isolation

> **核心原则：跨Actor访问必须显式await**

```swift
// ❌ 危险：@preconcurrency掩盖隔离违规
@preconcurrency
func syncWorkouts(completion: @escaping (Result<Void, Error>) -> Void) {
    backgroundQueue.async {
        let cache = UserWorkoutCache.shared  // 非Sendable!
        cache.store(workout)  // 跨Actor访问
    }
}

// ✅ 安全：使用Actor
actor UserWorkoutCache {
    func store(_ workout: Workout) { ... }
}

// ✅ 安全：使用async/await
func syncWorkouts() async throws {
    let cache = UserWorkoutCache.shared
    await cache.store(workout)  // 显式Actor跳转
}
```

### 7.3 Swift并发审查checklist

- [ ] 是否正确使用`@MainActor`？
- [ ] 是否有`@preconcurrency`掩盖问题？
- [ ] `asyncLet`变量是否在作用域内正确await？
- [ ] 跨Actor调用是否显式使用`await`？
- [ ] Sendable类型是否正确传递？
