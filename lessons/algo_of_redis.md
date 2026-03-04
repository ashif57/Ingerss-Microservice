Very good question 🔥
Now you're thinking like a **real DevOps / backend engineer**.

You configured:

* `maxmemory 50mb`
* `maxmemory-policy allkeys-lru`
* No TTL (removed `SETEX`)
* Hot data should stay forever (unless memory full)

Now you're asking:

> How exactly LRU is calculated?
> How does Redis decide which key to remove?

Let’s break this down properly.

---

# 🚀 First: When Does LRU Even Trigger?

Important:

👉 LRU does **NOT** run continuously.
👉 It runs **ONLY when memory reaches 50MB limit**.

Flow:

```
Redis memory < 50MB  → No eviction
Redis memory = 50MB  → Need space
                      ↓
               LRU selects victim key
                      ↓
                 Delete key
                      ↓
               Insert new key
```

So eviction happens **only when inserting new data** and memory is full.

---

# 🧠 What is LRU?

LRU = **Least Recently Used**

Meaning:

> Remove the key that has not been accessed for the longest time.

Access includes:

* GET
* SET
* HGET
* INCR
* Any read/write operation

---

# ⚙ How Redis Actually Calculates LRU

Important: Redis does NOT maintain a perfect linked list of usage.

Why?

Because that would be slow and expensive.

Instead, Redis uses:

> **Approximate LRU algorithm**

---

# 🔬 Internal Working (Real Mechanism)

Each key in Redis has:

* A small metadata field (LRU clock / last access time)

Redis keeps:

* 24-bit LRU time per key
* Global LRU clock (updated every 100ms)

When a key is accessed:

```
key.lru = current_global_lru_clock
```

So every key stores:

> "Last accessed timestamp"

---

# 🔥 What Happens When Memory is Full?

When inserting a new key:

1. Redis randomly samples a few keys (default: 5)
2. From those 5, it picks:
   👉 The one with the oldest last-access time
3. Deletes that key
4. Repeats if more space needed

This is called:

> **Approximate LRU using sampling**

---

# 🎯 Why Sampling?

If Redis checked ALL keys:

* O(N) operation
* Very slow
* Not scalable

Instead:

* It randomly picks small subset
* Chooses worst among them
* Very fast
* Good enough accuracy

---

# 📊 Example Scenario

Memory limit: 50MB
Current usage: 50MB

Keys in memory:

```
A (last used 1 sec ago)
B (last used 10 sec ago)
C (last used 1 hour ago)
D (last used 5 mins ago)
E (last used 2 days ago)
```

Redis samples 5 random keys:

Let's say sample = B, C, D, E, A

Oldest access time?

👉 E (2 days ago)

So Redis deletes key E.

---

# 🧠 Why Your "Hot Data" Will Stay

You removed TTL, so:

* Frequently accessed keys
* Always updated with latest LRU timestamp
* Never become "old"

So LRU naturally protects hot keys.

Your configuration is good for:

* API caching
* Frequently used payloads
* Stable traffic patterns

---

# ⚠ Important: What If All Keys Are Frequently Used?

Then eviction becomes semi-random.

If all keys are accessed constantly:

* Their LRU times are close
* Sampling may remove moderately active key

But this is rare unless traffic is uniform.

---

# 🔥 allkeys-lru vs volatile-lru

You set:

```
maxmemory-policy allkeys-lru
```

Meaning:

👉 ALL keys eligible for eviction.

If you had:

```
volatile-lru
```

Only keys with TTL would be removed.

Since you removed TTL, using volatile-lru would break your cache.

So your choice is correct ✅

---

# 🧪 How to See Eviction Stats

Run:

```
INFO stats
```

Look for:

```
evicted_keys
```

Also:

```
INFO memory
```

To see usage.

---

# 🧠 Advanced: Redis 4.0+ Improvement (LFU Option)

Redis also supports:

```
allkeys-lfu
```

LFU = Least Frequently Used

Instead of time-based:

* Tracks frequency counter
* Removes least frequently accessed key

Better for:

* Analytics
* Stable hot datasets

But slightly more memory overhead.

---

# 🔥 What Happens If Insertion Is Bigger Than Memory?

If new key size > available memory:

Redis may:

* Evict multiple keys
* Or reject write (if cannot free enough)

If eviction fails:

You’ll see:

```
OOM command not allowed when used memory > 'maxmemory'
```

---

# 🏗 Real Production Advice (For Your Setup)

Since you capped at 50MB:

Make sure:

1. Keys are not extremely large (huge JSON blobs)
2. Monitor eviction rate
3. Monitor hit ratio

Check hit rate:

```
keyspace_hits
keyspace_misses
```

Good cache = high hit ratio (above 80%)

---

# 🧠 Important Interview Question

Q: Is Redis LRU perfect?

Answer:

No. It uses approximate LRU with sampling for performance reasons.

---

# 🎯 What Happens Over Time in Your Setup?

Since you removed TTL:

* Frequently accessed payloads = stay forever
* Rarely used payloads = slowly evicted
* Memory remains capped at 50MB
* System stays stable

Your config is actually very production-friendly 👌

---

