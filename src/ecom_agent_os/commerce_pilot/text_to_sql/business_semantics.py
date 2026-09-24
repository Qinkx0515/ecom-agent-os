BUSINESS_SEMANTICS = """
You are working with an e-commerce analytics database.

Business metric definitions:

1. GMV
   - GMV means Gross Merchandise Value.
   - Calculate it from:
     order_items.quantity * order_items.unit_price
   - Only include orders where:
     orders.status = 'completed'
   - GMV is calculated before subtracting refunds.

2. Order count
   - Count distinct orders.id.
   - Only include completed orders unless the user explicitly
     requests another status.

3. Average order value
   - GMV / distinct completed order count.

4. Traffic
   - Use traffic_daily.visitors.

5. Conversion rate
   - SUM(traffic_daily.conversions)
     / NULLIF(SUM(traffic_daily.visitors), 0)

6. Refund amount
   - Use refunds.refund_amount.

7. Refund count
   - Count refunds.id.

8. Product category
   - Use products.category.

9. Product sales quantity
   - SUM(order_items.quantity).

10. Data clock
    - This project uses a snapshot dataset.
    - Relative time expressions MUST be anchored to the latest
      business date available in the database, NOT to the
      computer's CURRENT_DATE.
    - For order questions, derive the anchor date from:
      MAX(orders.order_date)::date
    - For traffic questions, derive it from:
      MAX(traffic_daily.date)
    - For refund questions, derive it from:
      MAX(refunds.created_at)::date

11. Time windows
    - "最近30天" means exactly 30 calendar days including
      the latest business date:
      [as_of_date - 29 days, as_of_date]
    - "前30天" means the immediately preceding 30 days:
      [as_of_date - 59 days, as_of_date - 30 days]

Important:
- Prefer explicit JOIN conditions using foreign keys.
- Never guess a column that does not exist.
- Never modify database data.
"""