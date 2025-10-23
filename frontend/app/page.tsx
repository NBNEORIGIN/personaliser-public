import OrdersTable from "../components/OrdersTable";

export default function Page() {
  return (
    <main className="min-h-screen" style={{ padding: 24, fontFamily: "system-ui, Arial" }}>
      <h1 style={{ fontSize: 24, marginBottom: 12 }}>Batch Personalisation — Prototype</h1>
      <div style={{display:'grid', gap:16}}>
        <section style={{border:'1px solid #ddd', borderRadius:8, padding:12}}>
          <h2 style={{marginTop:0}}>Amazon TXT</h2>
          <OrdersTable />
        </section>
        <section style={{border:'1px solid #ddd', borderRadius:8, padding:12}}>
          <h2 style={{marginTop:0}}>Hello</h2>
          <p>Second card placeholder.</p>
        </section>
      </div>
    </main>
  );
}
