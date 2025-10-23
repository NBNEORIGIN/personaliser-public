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

  return (
    <section>
      <h2 style={{marginBottom:8}}>Amazon TXT → Batch</h2>
      <div style={{display:'flex', gap:12, alignItems:'flex-start'}}>
        <div>
          <div>
            <textarea ref={taRef} rows={8} cols={60} placeholder={"Paste Amazon TXT (tab-delimited) incl. headers such as: amazon-order-id\tsku\tquantity\tcustomized-url"}></textarea>
          </div>
          <div style={{marginTop:6, display:'flex', gap:8}}>
            <button disabled={loadingIngest} onClick={onIngestFromPaste}>{loadingIngest? 'Parsing…':'Ingest from Paste'}</button>
            <input type="file" accept=".txt" onChange={onUploadFile}/>
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
        <div style={{flex:1}}>
          <h3>Items ({items.length})</h3>
          {items.length===0 ? (
            <div style={{opacity:0.8}}>No items yet. Paste TXT or upload a file to ingest.</div>
          ) : (
            <table border={1} cellPadding={6} style={{width:'100%', borderCollapse:'collapse'}}>
              <thead>
                <tr>
                  <th>#</th>
                  <th>order_ref</th>
                  <th>sku</th>
                  <th>template</th>
                  <th>graphics_key</th>
                  <th>colour</th>
                  <th>type</th>
                  <th>decoration</th>
                  <th>theme</th>
                  <th>photo</th>
                  <th>line_1</th>
                  <th>line_2</th>
                  <th>line_3</th>
                  <th>warnings</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it, idx)=>{
                  const map = Object.fromEntries((it.lines||[]).map(l=>[l.id, l.value]));
                  return (
                    <tr key={idx}>
                      <td>{idx+1}</td>
                      <td>{it.order_ref}</td>
                      <td>{it.sku||''}</td>
                      <td>{it.template_id||''}</td>
                      <td>{it.graphics_key||''}</td>
                      <td>{it.colour || '—'}</td>
                      <td>{it.product_type || '—'}</td>
                      <td>{it.decoration_type || '—'}</td>
                      <td>{it.theme || '—'}</td>
                      <td>
                        { (()=>{ const url = it.photo_asset_url || ''; const name = it.photo_filename || (url ? url.split('/').pop() || '' : '');
                          const abs = url ? (url.startsWith('http') ? url : `${API_BASE}${url}`) : '';
                          return url ? (
                            <div style={{display:'flex', alignItems:'center', gap:8}}>
                              <img src={abs} alt="photo" style={{height:40, objectFit:'cover', borderRadius:4}} />
                              <span title={name} style={{fontSize:12, color:'#666', maxWidth:160, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>
                                {name}
                              </span>
                            </div>
                          ) : '—'; })() }
                      </td>
                      <td>{map['line_1']||''}</td>
                      <td>{map['line_2']||''}</td>
                      <td>{map['line_3']||''}</td>
                      <td>
                        <div style={{display:'flex', gap:6, flexWrap:'wrap'}}>
                          {((it.decoration_type||'').toLowerCase()==='photo' && !(it.photo_asset_url||it.photo_asset_id)) && (
                            <span style={{background:'#ef4444', color:'#fff', padding:'2px 6px', borderRadius:4, fontSize:12}}>PHOTO_MISSING</span>
                          )}
                          {((it.decoration_type||'').toLowerCase()==='graphic' && !(it.graphics_key)) && (
                            <span style={{background:'#f59e0b', color:'#fff', padding:'2px 6px', borderRadius:4, fontSize:12}}>GRAPHIC_MISSING</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
          <div style={{marginTop:10}}>
            <button disabled={loadingGen || items.length===0} onClick={onGenerate}>{loadingGen? 'Generating…':'Generate Job'}</button>
          </div>
          {bedPreview && (
            <div style={{marginTop:12}}>
              {/\.png$/i.test(bedPreview) ? (
                <img src={bedPreview} width={480} alt="bed preview"/>
              ) : (
                <a href={bedPreview} target="_blank" rel="noreferrer">Open bed SVG</a>
              )}
              <div style={{marginTop:6}}>
                <strong>Artifacts:</strong>
                <ul>
                  {artifacts.map((a)=> (<li key={a}><a href={a} target="_blank" rel="noreferrer">{a}</a></li>))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
