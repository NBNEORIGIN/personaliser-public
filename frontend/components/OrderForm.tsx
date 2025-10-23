"use client";
import { useState } from "react";
import { previewItem } from "../lib/api";

export default function OrderForm({ onAdd }:{ onAdd:(item:any)=>void }){
  const [l1,setL1]=useState("In loving memory");
  const [l2,setL2]=useState("John K Newman");
  const [l3,setL3]=useState("1950–2024");
  const [img,setImg]=useState<string|undefined>();

  async function onPreview(){
    const item = { template_id: "PLAQUE-140x90-V1", lines:[
      {id:"line_1", value:l1},{id:"line_2", value:l2},{id:"line_3", value:l3}
    ]};
    const res = await previewItem(item);
    setImg(res.preview_url);
  }

  return (
    <section style={{marginTop:20, marginBottom:20}}>
      <h2>Single Item Preview</h2>
      <div>
        <input value={l1} onChange={e=>setL1(e.target.value)} placeholder="Line 1" />
      </div>
      <div>
        <input value={l2} onChange={e=>setL2(e.target.value)} placeholder="Line 2" />
      </div>
      <div>
        <input value={l3} onChange={e=>setL3(e.target.value)} placeholder="Line 3" />
      </div>
      <div style={{display:"flex", gap:8, marginTop:8}}>
        <button onClick={onPreview}>Preview</button>
        <button onClick={()=>onAdd({ template_id: "PLAQUE-140x90-V1", lines:[
          {id:"line_1", value:l1},{id:"line_2", value:l2},{id:"line_3", value:l3}
        ]})}>Add to Batch</button>
      </div>
      {img && (<div style={{marginTop:10}}><img src={img} alt="preview" width={360}/></div>)}
    </section>
  )
}
