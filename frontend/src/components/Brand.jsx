import React from 'react';
export default function Brand({compact=false}){
  return <span className="brand"><img src="/brand/veyra-official.webp" width="34" height="34" alt=""/><span>veyra<span className="brand-ai">ai</span></span>{!compact&&<span className="version">0.4.2 <span className="sr-only">review candidate</span></span>}</span>;
}
