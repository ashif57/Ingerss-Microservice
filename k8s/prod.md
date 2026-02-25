```
KIND + NGINX Ingress  (local)
        ↓
EKS + AWS ALB Ingress (production)
```

Now the BIG question:

> ✅ If I use Amazon ALB, what changes in my Ingress YAML?

---

# 🧠 First — Architecture Change

## 🔵 Local (what you used)

```
User
 ↓
NGINX Ingress Controller (pod)
 ↓
Services → Pods
```

---

## 🟢 Production (EKS with ALB)

```
User
 ↓
AWS ALB (created automatically)
 ↓
AWS Load Balancer Controller
 ↓
Kubernetes Services → Pods
```

👉 **ALB itself becomes the ingress.**
NGINX is usually NOT needed.

---

# ✅ Step 1 — Install AWS Load Balancer Controller

In EKS you install:

```
AWS Load Balancer Controller
```

This controller watches Ingress objects and creates ALB automatically.

---

# ✅ Step 2 — Main Change in Ingress YAML

You only change **annotations + ingressClassName**.

---

## 🔴 Your Current (NGINX)

```yaml
metadata:
  name: ingress-3tier
spec:
  ingressClassName: nginx
```

---

## 🟢 Production Version (ALB)

### ✅ Updated Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-3tier
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  ingressClassName: alb
  rules:
    - host: company.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: react-service
                port:
                  number: 80

          - path: /api/node
            pathType: Prefix
            backend:
              service:
                name: nodebackend-service
                port:
                  number: 80

          - path: /api/fastapi
            pathType: Prefix
            backend:
              service:
                name: fastapi-service
                port:
                  number: 80
```

---

# ✅ Step 3 — Add SSL Certificate (VERY IMPORTANT)

Create certificate in:

```
AWS Certificate Manager (ACM)
```

Then add annotation:

```yaml
alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:REGION:ACCOUNT:certificate/xxxxx
```

Now ALB handles HTTPS automatically.

---

# ✅ Step 4 — Backend Services (NO CHANGE)

Keep services as:

```yaml
type: ClusterIP
```

Backend remains PRIVATE.

---

# 🔥 What Happens After `kubectl apply`

AWS controller automatically:

1️⃣ Creates ALB
2️⃣ Creates Target Groups
3️⃣ Registers Pods
4️⃣ Attaches SSL cert
5️⃣ Opens HTTPS endpoint

You will see:

```bash
kubectl get ingress
```

```
ADDRESS: xxxx.elb.amazonaws.com
```

---

# 🧩 Request Flow in Production

```
Browser
   ↓ HTTPS
AWS ALB
   ↓
Target Group
   ↓
K8s Service
   ↓
Pod
```

---

# ⭐ BIG Difference (Remember)

| NGINX               | ALB                |
| ------------------- | ------------------ |
| Runs inside cluster | AWS managed        |
| You manage scaling  | AWS scales         |
| TLS inside pod      | TLS at ALB         |
| NodePort used       | Direct pod routing |

---

# 🚨 IMPORTANT CHANGE FOR YOUR REACT APP

Now React should call:

```
/api/node
/api/fastapi
```

NOT localhost.

Because domain becomes:

```
https://company.com
```

---

# ✅ Interview Golden Line

> “In EKS we replace NGINX ingress with AWS Load Balancer Controller, which dynamically provisions an ALB based on Kubernetes ingress annotations.”

---
