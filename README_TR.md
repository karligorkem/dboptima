# DBOptima

[English README](README.md)

DBOptima, PostgreSQL sorgularını analiz eden, indeks adayları üreten, bu adayları gerçek benchmark sonuçlarıyla test eden ve ölçülen sonuçları kaydeden bir sorgu optimizasyon projesidir.

Proje; deterministik PostgreSQL plan analizi ile, benchmark öncesinde adayları sıralamak için kullanılan bir makine öğrenmesi modelini birleştirir. Nihai öneri durumu model tahminine göre değil, gerçek benchmark sonucuna göre belirlenir.

---

## Ne Yapıyor?

Kullanıcı tarafından verilen bir SQL sorgusu için DBOptima şunları yapabilir:

- `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` çalıştırır
- execution plan bilgisini inceler
- sequential scan tespit eder
- indeks adayları üretir
- adayları ML modeliyle sıralar
- geçici indeks öncesi ve sonrası sorgu gecikmesini ölçer
- gerçek performans artışını hesaplar
- sonucu `RECOMMENDED`, `REVIEW` veya `REJECTED` olarak sınıflandırır
- sorgu, plan, benchmark, öneri ve eğitim verilerini kaydeder

Ana akış:

```text
SQL Sorgusu
   |
   v
EXPLAIN ANALYZE
   |
   v
Plan Analizi
   |
   v
İndeks Adayı Üretimi
   |
   v
ML ile Aday Sıralama
   |
   v
Önce / Sonra Benchmark
   |
   v
Ölçülen Performans Artışı
   |
   v
Öneri Kararı
```

ML modeli adayları önceliklendirmek için kullanılır. Son karar gerçek PostgreSQL benchmark sonucuna dayanır.

---

## Öneri Politikası

Mevcut karar eşikleri:

| Ölçülen performans artışı | Durum |
| --- | --- |
| `>= 20%` | `RECOMMENDED` |
| `>= 5%` ve `< 20%` | `REVIEW` |
| `< 5%` | `REJECTED` |

---

## Örnek Sorgu

Örnek sorgu:

```sql
SELECT *
FROM orders
WHERE customer_id = 42
  AND status = 'PAID'
ORDER BY created_at DESC;
```

Bu sorgu için şu alanlar etrafında bir indeks adayı üretilebilir:

```text
customer_id
status
created_at DESC
```

Mevcut local test veritabanında bu sorgu, önerilen composite index sonrasında oldukça yüksek performans artışı göstermiştir.

Kesin sonuçlar;

- veri boyutuna
- cache durumuna
- donanıma
- PostgreSQL istatistiklerine
- execution plan kararlarına

göre değişebilir.

---

## Makine Öğrenmesi

DBOptima şu anda aday sıralama için V2 modelini kullanır.

```text
Model sürümü:      v2-final
Feature şeması:    v2
Feature sayısı:    26
Eğitim örneği:     340
Query grubu:       51
```

### Değerlendirme

Mevcut deneysel veri seti üzerindeki grouped validation sonuçları:

| Metrik | Sonuç |
| --- | ---: |
| MAE | `10.50 ± 2.88` |
| RMSE | `16.74 ± 2.81` |
| R² | `0.816 ± 0.095` |
| Durum doğruluğu | `78.91% ± 5.31%` |

Daha önce görülmeyen query grupları için cold-start değerlendirmesi:

| Metrik | Sonuç |
| --- | ---: |
| MAE | `16.13` |
| RMSE | `22.51` |
| R² | `0.7425` |
| Durum doğruluğu | `70.59%` |

Bu metrikler yalnızca mevcut proje veri setini ifade eder. Farklı PostgreSQL şemaları ve iş yükleri için genel başarı garantisi değildir.

---

## Mimari

```text
+----------------------+
|      Next.js UI      |
|----------------------|
| Overview             |
| Query Analyzer       |
| Recommendations      |
| Benchmarks           |
| Workload             |
| Models               |
| Databases            |
| Settings             |
+----------+-----------+
           |
           v
+----------+-----------+
|      FastAPI API     |
+----------+-----------+
           |
     +-----+-----+
     |           |
     v           v
Plan Analyzer   ML Ranker
     |           |
     +-----+-----+
           |
           v
    Index Advisor
           |
           v
   Benchmark Engine
      /         \
     v           v
Target DB    Metadata DB
PostgreSQL   PostgreSQL
```

---

## Kullanılan Teknolojiler

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy
- psycopg
- Pydantic
- PostgreSQL
- scikit-learn
- joblib
- Alembic

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Lucide React
- Recharts

### Altyapı

- Docker
- Docker Compose
- PostgreSQL 17

---

## Proje Yapısı

```text
dboptima/
├── backend/
│   ├── app/
│   │   ├── analyzers/
│   │   ├── api/
│   │   ├── benchmark/
│   │   ├── collectors/
│   │   ├── core/
│   │   ├── db/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── recommenders/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── analyzer/
│   │       ├── recommendations/
│   │       ├── benchmarks/
│   │       ├── workload/
│   │       ├── models/
│   │       ├── databases/
│   │       ├── settings/
│   │       ├── components/
│   │       ├── lib/
│   │       └── page.tsx
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## Ana Sayfalar

### Overview

Genel sistem metriklerini gösterir:

- analiz edilen sorgu sayısı
- query call sayısı
- recommendation sayıları
- latency sample sayısı
- ölçülen performans artışı
- son öneriler

### Query Analyzer

Ana optimizasyon ekranıdır.

Gösterilen bilgiler:

- execution time
- planning time
- bulunan plan problemleri
- indeks adayları
- tahmin edilen gain
- ölçülen gain
- recommendation durumu

### Recommendations

Kaydedilmiş öneri geçmişini, filtreleme ve detay görünümüyle gösterir.

### Benchmarks

Gerçek before/after benchmark sonuçlarını gösterir.

### Workload

Query bazlı istatistikleri gösterir:

- total calls
- average latency
- p95 latency
- max latency
- recommendation count
- best measured gain

### Models

Production model metadata ve feature bilgilerini gösterir.

### Databases

Kayıtlı PostgreSQL bağlantılarını ve bağlantı testlerini gösterir.

### Settings

Mevcut recommendation ve benchmark politikalarını gösterir.

---

## Local Geliştirme

### Gereksinimler

Kurulu olması gerekenler:

- Python 3.12+
- Node.js
- npm
- Docker Desktop
- Git

### 1. PostgreSQL containerlarını başlat

Proje kök dizininde:

```bash
docker compose up -d
```

Kontrol:

```bash
docker ps
```

### 2. Backend

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

Beklenen cevap:

```json
{
  "status": "ok"
}
```

### 3. Frontend

Şu dosyayı oluştur:

```text
frontend/.env.local
```

Örnek:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Ardından:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## Ana API Endpointleri

```text
GET  /health

GET  /api/databases
POST /api/databases
POST /api/databases/{database_id}/test

POST /api/databases/{database_id}/analyze-query
POST /api/databases/{database_id}/optimize-query
POST /api/databases/{database_id}/benchmark-index

GET  /api/overview/{database_id}
GET  /api/recommendations/{database_id}
GET  /api/benchmarks/{database_id}
GET  /api/workload/{database_id}

GET  /api/models/production
GET  /api/settings
```

---

## Örnek Optimizasyon İsteği

```http
POST /api/databases/2/optimize-query
Content-Type: application/json
```

```json
{
  "query": "SELECT * FROM orders WHERE customer_id = 42 AND status = 'PAID' ORDER BY created_at DESC"
}
```

Response içinde şu bölümler bulunur:

```text
baseline
issues
candidate_count
evaluation_context
candidates
persistence
```

Candidate sonuçları şu alanları içerebilir:

```text
ml_rank
actual_rank
ml_prediction
benchmark
decision
prediction_error_percent
```

Bu yapı sayesinde ML sıralaması ile gerçek PostgreSQL benchmark sıralaması karşılaştırılabilir.

---

## Kaydedilen Veriler

DBOptima şu tür bilgileri persist eder:

- database connections
- normalized queries
- query execution samples
- query plans
- recommendations
- benchmark results
- ML training samples

Query history tarafında şu metrikler tutulur:

- total calls
- average latency
- minimum latency
- maximum latency
- p95 latency
- first seen
- last seen

---

## Mevcut Sınırlamalar

Bu proje şu anda geliştirme / portföy amaçlı bir prototiptir.

Mevcut sınırlamalar:

- ML veri seti sınırlı bir geliştirme workload'una dayanır
- farklı ve rastgele PostgreSQL şemalarındaki davranışı henüz kanıtlanmış değildir
- query fingerprinting yaklaşımı hafiftir
- optimizasyon işlemleri şu anda senkron çalışır
- authentication yoktur
- multi-user yapı yoktur
- workload-wide index portfolio optimization henüz yoktur
- production observability henüz yoktur

Benchmark işlemleri için local, test, staging, clone veya kontrollü bir PostgreSQL veritabanı kullanılması önerilir.

---

## Gelecek Geliştirmeler

Olası sonraki adımlar:

- asynchronous benchmark jobs
- daha güçlü SQL parsing
- redundant index detection
- unused index analysis
- table statistics recommendations
- query rewrite candidates
- daha zengin workload istatistikleri
- model version tracking
- model retraining workflow
- drift detection
- benchmark budget management
- workload-wide index selection
- CP-SAT tabanlı index portfolio optimization
- authentication / authorization
- automated tests
- Testcontainers
- production observability

---

## Geliştirme Durumu

Tamamlanan ana parçalar:

- PostgreSQL connection management
- execution plan collection
- sequential scan analysis
- index candidate generation
- real before/after benchmark flow
- recommendation classification
- query fingerprinting
- query history
- latency sample persistence
- recommendation history
- ML training sample persistence
- V2 feature schema
- V2 model evaluation
- production V2 model artifact
- ML candidate ranking
- benchmark vs prediction comparison
- Overview UI
- Query Analyzer UI
- Recommendations UI
- Benchmarks UI
- Workload UI
- Models UI
- Databases UI
- Settings UI

---

## Notlar

Gerçek credential bilgilerini veya local environment dosyalarını commit etmeyin.

Önerilen `.gitignore` girdileri:

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/

.env
.env.*
!.env.example

frontend/node_modules/
frontend/.next/
frontend/out/
frontend/.env.local

.vscode/
.idea/

.DS_Store
Thumbs.db
```

Model artifact dosyaları repository içinde tutulacaksa yalnızca mevcut uygulamayı çalıştırmak için gereken dosyaların eklenmesi daha temiz olur.

---

## Geliştirici

Backend geliştirme, PostgreSQL query-plan analizi, benchmark, makine öğrenmesi, veri kalıcılığı ve frontend geliştirmeyi bir araya getiren full-stack bir veritabanı optimizasyon projesi olarak geliştirilmiştir.
