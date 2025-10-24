import OrdersTable from "../components/OrdersTable";

export default function Page() {
  return (
    <main style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    }}>
      {/* Header */}
      <header style={{
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(0,0,0,0.1)',
        padding: '20px 32px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ 
              fontSize: 28, 
              fontWeight: 700, 
              margin: 0,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>NBNE Personaliser</h1>
            <p style={{ margin: '4px 0 0 0', color: '#666', fontSize: 14 }}>Automated Batch Production System</p>
          </div>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600
          }}>PROTOTYPE v1.0</div>
        </div>
      </header>

      {/* Main Content */}
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '32px' }}>
        <section style={{
          background: 'white',
          borderRadius: 16,
          padding: 32,
          boxShadow: '0 8px 32px rgba(0,0,0,0.12)'
        }}>
          <OrdersTable />
        </section>

        {/* Info Footer */}
        <div style={{
          marginTop: 24,
          padding: 20,
          background: 'rgba(255,255,255,0.9)',
          borderRadius: 12,
          textAlign: 'center',
          color: '#555',
          fontSize: 13
        }}>
          <p style={{ margin: 0 }}>🚀 Streamlining memorial production with intelligent automation</p>
        </div>
      </div>
    </main>
  );
}
