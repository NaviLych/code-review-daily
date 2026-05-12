# 架构模式库

> 积累跨语言的架构设计模式和设计智慧

---

## 一、并发架构模式

### 1.1 CSP vs Actor模式对比

| 维度 | CSP (Go) | Actor (Rust/Elixir) |
|------|----------|---------------------|
| **通信方式** | Channel传递消息 | 消息队列+邮箱 |
| **解耦程度** | 生产者-消费者 | 完全解耦 |
| **错误处理** | 手动处理 | 内置监督机制 |
| **适用场景** | 轻量并发、流水线 | 复杂状态、容错系统 |

### 1.2 Go CSP实现

```go
// 流水线模式
func pipeline(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for v := range in {
            out <- process(v)
        }
        close(out)
    }()
    return out
}
```

### 1.3 Rust Actor实现

```rust
// 使用Tokio的mpsc模拟Actor
struct Counter(u64);

impl Counter {
    fn inc(&mut self) { self.0 += 1; }
    fn get(&self) -> u64 { self.0 }
}
```

---

## 二、依赖注入模式

### 2.1 TypeScript实现

```typescript
interface Logger { log(msg: string): void; }
interface Database { query(sql: string): any[]; }

class Service {
    constructor(
        private logger: Logger,
        private db: Database
    ) {}
}
```

### 2.2 Swift实现

```swift
protocol Logger { func log(_ msg: String) }
protocol Database { func query(_ sql: String) -> [Any] }

class Service {
    private let logger: Logger
    private let db: Database
    
    init(logger: Logger, db: Database) {
        self.logger = logger
        self.db = db
    }
}
```

### 2.3 跨语言启示

```
✅ 共同点：
- 接口/协议定义抽象
- 构造函数注入依赖
- 便于单元测试Mock
- 解耦核心逻辑

💡 设计启示：
依赖注入的核心是"控制反转"，不同语言的语法不同，思路一致
```

---

## 三、泛型抽象模式

### 3.1 泛型工厂模式

```typescript
// TypeScript: 类型安全的工厂
class Factory<T> {
    create(ctor: new () => T): T {
        return new ctor();
    }
}
```

```swift
// Swift: 协议约束
protocol Buildable { init() }
class Factory<T: Buildable> {
    func create() -> T { return T() }
}
```

### 3.2 泛型Repository模式

```typescript
// TypeScript: 统一数据访问
interface Entity { id: string; }
interface Repository<T extends Entity> {
    findById(id: string): Promise<T | null>;
    save(entity: T): Promise<T>;
    delete(id: string): Promise<void>;
}
```

### 3.3 跨语言对比

| 模式 | TypeScript | Swift | Rust |
|------|------------|-------|------|
| 泛型约束 | `<T extends X>` | `<T: X>` | `<T: X>` |
| 多重约束 | `T extends A & B` | `T: A & B` | `T: A + B` |
| where子句 | 无 | 有 | 有 |

---

## 四、错误处理模式

### 4.1 Go错误处理

```go
// ✅ 显式错误检查
result, err := doSomething()
if err != nil {
    return fmt.Errorf("doSomething failed: %w", err)
}

// ❌ 忽略错误
result, _ := doSomething()
```

### 4.2 Rust Result模式

```rust
// ✅ 组合器链式处理
let result = fetch()
    .map_err(|e| MyError::Fetch(e))?
    .parse::<i32>()
    .map_err(|e| MyError::Parse(e))?;

// ❌ unwrap滥用
let result = fetch().unwrap(); // panic风险
```

### 4.3 Swift Result类型

```swift
// ✅ Result类型
func fetch() -> Result<Data, Error> {
    // ...
}

switch fetch() {
case .success(let data): // 处理数据
case .failure(let error): // 处理错误
}
```

### 4.4 跨语言启示

```
Go:        显式检查 → if err != nil
Rust:      穷尽匹配 → match/if let/?
Swift:     Result枚举 + try/catch
           ↓
核心思想: 错误是值，不是异常
```

---

## 五、资源管理模式

### 5.1 RAII vs defer

| 语言 | 机制 | 特点 |
|------|------|------|
| Rust | RAII + Drop trait | 编译期保证 |
| Swift | defer | 作用域结束时执行 |
| Go | defer | 后进先出 |
| C++ | RAII + destructor | 构造函数获取 |

### 5.2 示例对比

```rust
// Rust RAII
struct File { /* ... */ }
impl Drop for File {
    fn drop(&mut self) { self.close(); }
}
// 离开作用域自动关闭
```

```swift
// Swift defer
func read() {
    let file = open()
    defer { close(file) }
    // ...
}
```

```go
// Go defer
func read() {
    file, _ := open()
    defer file.Close()
    // ...
}
```

### 5.3 设计启示

```
💡 核心思想: 资源获取与释放配对
   ↓
不同语言用不同语法实现同一原则：
- Rust: 类型系统 + 编译期检查
- Swift/Go: 关键字 + 运行时保证
- C++: RAII传统
```

---

## 六、持续更新

- **Day 1**: 函数式编程架构、Swift protocol-oriented编程
- **Day 2**: CSP vs Actor、Rust vs Go并发对比、泛型抽象模式
- **Day 3**: 待补充...
