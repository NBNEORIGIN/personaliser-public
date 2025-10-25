"use client";
import { useRef, useState } from "react";
import { generateJob, ingestAmazon, IngestItem, API_BASE } from "../lib/api";

export default function OrdersTable(){
  const [loadingIngest, setLoadingIngest] = useState(false);
  const [loadingGen, setLoadingGen] = useState(false);
  const [items, setItems] = useState<IngestItem[]>([]);
  const [warnings, setWarnings] = useState<any[]>([]);
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [bedPreview, setBedPreview] = useState<string|undefined>();
  const taRef = useRef<HTMLTextAreaElement>(null);

  async function onIngestFromPaste(){
    setLoadingIngest(true);
    setWarnings([]);
    try{
      const text = taRef.current?.value || "";
      const res = await ingestAmazon({ text });
      setItems(res.items || []);
      setWarnings(res.warnings || []);
    }catch(e:any){
      alert(e?.message||String(e));
    }finally{ setLoadingIngest(false); }
  }

  async function onUploadFile(e:React.ChangeEvent<HTMLInputElement>){
    const f = e.target.files?.[0];
    if(!f) return;
    setLoadingIngest(true);
    setWarnings([]);
    try{
      const res = await ingestAmazon({ file: f });
      setItems(res.items || []);
      setWarnings(res.warnings || []);
    }catch(e:any){
      alert(e?.message||String(e));
    }finally{ setLoadingIngest(false); e.target.value = ""; }
  }

  function badge(w:any){
    const color = w.severity==='error' ? '#ef4444' : w.severity==='warn' ? '#f59e0b' : '#3b82f6';
    return <span style={{background:color, color:'white', padding:'2px 6px', borderRadius:4, fontSize:12}}>{w.code}</span>
  }

  function toOrderItems(its:IngestItem[]){
    return its.map(it=>({
      template_id: it.template_id || 'PLAQUE-140x90-V1',
      lines: [
        { id:'line_1', value: it.lines.find(l=>l.id==='line_1')?.value || '' },
        { id:'line_2', value: it.lines.find(l=>l.id==='line_2')?.value || '' },
        { id:'line_3', value: it.lines.find(l=>l.id==='line_3')?.value || '' },
      ],
      order_ref: it.order_ref,
      channel: 'amazon',
      // Pass through enrichment fields so backend processors can route and place graphics
      sku: it.sku || '',
      graphics_key: it.graphics_key || '',
      colour: it.colour || '',
      product_type: it.product_type || '',
      decoration_type: it.decoration_type || '',
      theme: it.theme || ''
    }));
  }

  async function onGenerate(){
    setLoadingGen(true);
    setArtifacts([]);
    setBedPreview(undefined);
    try{
      const res = await generateJob(toOrderItems(items));
      if(res.status===422){
        const errs = res.data?.warnings || res.data?.detail?.warnings;
        alert("Errors in items: " + JSON.stringify(errs));
        return;
      }
      const data = res.data || {};
      const arts: string[] = data.artifacts || [];
      const absArts = arts.map(a => a && a.startsWith("http") ? a : (a ? `${API_BASE}${a}` : a));
      setArtifacts(absArts);
      const png = absArts.find(a=>/bed_\d+\.png$/i.test(a));
      const svg = absArts.find(a=>/bed_\d+\.svg$/i.test(a));
      setBedPreview(png || undefined);
      if(!png && svg) setBedPreview(svg);
    }catch(e:any){
      alert(e?.message||String(e));
    }finally{ setLoadingGen(false); }
  }

  const buttonStyle = {
    padding: '10px 20px',
    borderRadius: 8,
    border: 'none',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: 14,
    transition: 'transform 0.2s, box-shadow 0.2s',
    boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)'
  };

  const disabledButtonStyle = {
    ...buttonStyle,
    opacity: 0.5,
    cursor: 'not-allowed'
  };

  return (
    <section>
      <h2 style={{
        marginBottom: 24,
        fontSize: 22,
        fontWeight: 700,
        color: '#1a202c',
        borderBottom: '2px solid #e2e8f0',
        paddingBottom: 12
      }}>Amazon Order Import</h2>
      
      <div style={{display:'grid', gridTemplateColumns: '400px 1fr', gap:24, alignItems:'start'}}>
        {/* Left: Input Section */}
        <div style={{
          background: '#f7fafc',
          padding: 20,
          borderRadius: 12,
          border: '1px solid #e2e8f0'
        }}>
          <h3 style={{marginTop: 0, fontSize: 16, fontWeight: 600, color: '#2d3748', marginBottom: 12}}>Import Data</h3>
          <div>
            <textarea 
              ref={taRef} 
              rows={10} 
              style={{
                width: '100%',
                padding: 12,
                borderRadius: 8,
                border: '2px solid #e2e8f0',
                fontSize: 13,
                fontFamily: 'monospace',
                resize: 'vertical',
                outline: 'none',
                transition: 'border-color 0.2s'
              }}
              placeholder={"Paste Amazon TXT (tab-delimited) incl. headers such as:\namazon-order-id\tsku\tquantity\tcustomized-url"}
              onFocus={(e) => e.target.style.borderColor = '#667eea'}
              onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
            />
          </div>
          <div style={{marginTop:12, display:'flex', flexDirection: 'column', gap:10}}>
            <button 
              disabled={loadingIngest} 
              onClick={onIngestFromPaste}
              style={loadingIngest ? disabledButtonStyle : buttonStyle}
              onMouseEnter={(e) => !loadingIngest && (e.currentTarget.style.transform = 'translateY(-2px)')}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              {loadingIngest? '⏳ Parsing…':'📥 Ingest from Paste'}
            </button>
            <div style={{textAlign: 'center', color: '#718096', fontSize: 13, margin: '8px 0'}}>or</div>
            <label style={{
              ...buttonStyle,
              background: 'white',
              color: '#667eea',
              border: '2px solid #667eea',
              display: 'block',
              textAlign: 'center',
              cursor: 'pointer'
            }}>
              📁 Upload TXT File
              <input type="file" accept=".txt" onChange={onUploadFile} style={{display: 'none'}}/>
            </label>
          </div>
          {warnings.length>0 && (
            <div style={{marginTop:8}}>
              <strong>Warnings:</strong>
              <ul>
                {warnings.map((w:any, idx:number)=> (
                  <li key={idx} style={{display:'flex', gap:6, alignItems:'center'}}>{badge(w)} <span>{w.message}</span></li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        {/* Right: Results Section */}
        <div style={{flex:1}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
            <h3 style={{margin: 0, fontSize: 18, fontWeight: 600, color: '#2d3748'}}>
              Items <span style={{
                background: items.length > 0 ? '#48bb78' : '#cbd5e0',
                color: 'white',
                padding: '2px 10px',
                borderRadius: 12,
                fontSize: 14,
                fontWeight: 700,
                marginLeft: 8
              }}>{items.length}</span>
            </h3>
            {items.length > 0 && (
              <button 
                disabled={loadingGen} 
                onClick={onGenerate}
                style={loadingGen ? disabledButtonStyle : buttonStyle}
                onMouseEnter={(e) => !loadingGen && (e.currentTarget.style.transform = 'translateY(-2px)')}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                {loadingGen? '⚙️ Generating…':'✨ Generate Job'}
              </button>
            )}
          </div>
          {items.length===0 ? (
            <div style={{
              padding: 40,
              textAlign: 'center',
              background: '#f7fafc',
              borderRadius: 12,
              border: '2px dashed #cbd5e0',
              color: '#718096'
            }}>
              <div style={{fontSize: 48, marginBottom: 12}}>📋</div>
              <div style={{fontSize: 16, fontWeight: 500}}>No items yet</div>
              <div style={{fontSize: 14, marginTop: 8}}>Paste TXT or upload a file to get started</div>
            </div>
          ) : (
            <div style={{overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 8}}>
              <table style={{width:'100%', borderCollapse:'collapse', fontSize: 13}}>
                <thead>
                  <tr style={{background: '#f7fafc'}}>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>#</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Order Ref</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>SKU</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Graphics</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Colour</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Type</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Line 1</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Line 2</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Line 3</th>
                    <th style={{padding: 12, textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0'}}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it, idx)=>{
                    const map = Object.fromEntries((it.lines||[]).map(l=>[l.id, l.value]));
                    const hasIssue = ((it.decoration_type||'').toLowerCase()==='photo' && !(it.photo_asset_url||it.photo_asset_id)) ||
                                     ((it.decoration_type||'').toLowerCase()==='graphic' && !(it.graphics_key));
                    return (
                      <tr key={idx} style={{borderBottom: '1px solid #e2e8f0', background: idx % 2 === 0 ? 'white' : '#fafafa'}}>
                        <td style={{padding: 12, color: '#718096'}}>{idx+1}</td>
                        <td style={{padding: 12, fontWeight: 500, color: '#2d3748'}}>{it.order_ref}</td>
                        <td style={{padding: 12, color: '#4a5568', fontFamily: 'monospace', fontSize: 12}}>{it.sku||'—'}</td>
                        <td style={{padding: 12, color: '#4a5568'}}>{it.graphics_key||'—'}</td>
                        <td style={{padding: 12}}>
                          <span style={{
                            background: it.colour ? '#e6fffa' : '#f7fafc',
                            color: it.colour ? '#047857' : '#718096',
                            padding: '4px 8px',
                            borderRadius: 4,
                            fontSize: 11,
                            fontWeight: 600,
                            textTransform: 'uppercase'
                          }}>{it.colour || 'None'}</span>
                        </td>
                        <td style={{padding: 12, color: '#4a5568', fontSize: 12}}>{it.decoration_type || '—'}</td>
                        <td style={{padding: 12, color: '#2d3748'}}>{map['line_1']||'—'}</td>
                        <td style={{padding: 12, color: '#2d3748'}}>{map['line_2']||'—'}</td>
                        <td style={{padding: 12, color: '#2d3748'}}>{map['line_3']||'—'}</td>
                        <td style={{padding: 12}}>
                          {hasIssue ? (
                            <span style={{background:'#fed7d7', color:'#c53030', padding:'4px 8px', borderRadius:4, fontSize:11, fontWeight:600}}>⚠️ Issue</span>
                          ) : (
                            <span style={{background:'#c6f6d5', color:'#22543d', padding:'4px 8px', borderRadius:4, fontSize:11, fontWeight:600}}>✓ Ready</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          {artifacts.length > 0 && (
            <div style={{marginTop:20, padding:20, background:'#f7fafc', borderRadius:8}}>
              <h3 style={{marginBottom:16, fontSize:18, fontWeight:600}}>Generated Artifacts</h3>
              <table style={{width:'100%', borderCollapse:'collapse', background:'white', borderRadius:8, overflow:'hidden', boxShadow:'0 1px 3px rgba(0,0,0,0.1)'}}>
                <thead>
                  <tr style={{background:'#edf2f7', borderBottom:'2px solid #e2e8f0'}}>
                    <th style={{padding:12, textAlign:'left', fontSize:12, fontWeight:600, color:'#4a5568'}}>Type</th>
                    <th style={{padding:12, textAlign:'left', fontSize:12, fontWeight:600, color:'#4a5568'}}>Processor</th>
                    <th style={{padding:12, textAlign:'left', fontSize:12, fontWeight:600, color:'#4a5568'}}>File</th>
                    <th style={{padding:12, textAlign:'center', fontSize:12, fontWeight:600, color:'#4a5568'}}>Preview</th>
                    <th style={{padding:12, textAlign:'center', fontSize:12, fontWeight:600, color:'#4a5568'}}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {artifacts.map((url, idx) => {
                    const filename = url.split('/').pop() || '';
                    const isSvg = /\.svg$/i.test(filename);
                    const isCsv = /\.csv$/i.test(filename);
                    const processorMatch = filename.match(/_([a-z_]+_v\d+)_/);
                    const processor = processorMatch ? processorMatch[1] : 'unknown';
                    const type = isSvg ? 'SVG' : isCsv ? 'CSV' : 'File';
                    
                    return (
                      <tr key={idx} style={{borderBottom:'1px solid #e2e8f0'}}>
                        <td style={{padding:12}}>
                          <span style={{
                            background: isSvg ? '#e6fffa' : '#fef5e7',
                            color: isSvg ? '#047857' : '#d97706',
                            padding:'4px 8px',
                            borderRadius:4,
                            fontSize:11,
                            fontWeight:600
                          }}>{type}</span>
                        </td>
                        <td style={{padding:12, fontSize:12, color:'#4a5568', fontFamily:'monospace'}}>{processor}</td>
                        <td style={{padding:12, fontSize:11, color:'#718096', fontFamily:'monospace', maxWidth:200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{filename}</td>
                        <td style={{padding:12, textAlign:'center'}}>
                          {isSvg && (
                            <a href={url} target="_blank" rel="noreferrer" style={{color:'#667eea', textDecoration:'none', fontSize:12}}>
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{display:'inline-block', verticalAlign:'middle'}}>
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                              </svg>
                              <span style={{marginLeft:4}}>View</span>
                            </a>
                          )}
                        </td>
                        <td style={{padding:12, textAlign:'center'}}>
                          <a href={url} download style={{
                            background:'#667eea',
                            color:'white',
                            padding:'6px 12px',
                            borderRadius:4,
                            fontSize:11,
                            fontWeight:600,
                            textDecoration:'none',
                            display:'inline-block'
                          }}>Download</a>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
