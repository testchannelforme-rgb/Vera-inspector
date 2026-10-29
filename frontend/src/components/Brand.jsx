import React from 'react';
export default function Brand({compact=false}){
  return <span className="brand"><img src="/brand/veyra-prism.svg" width="34" height="34" alt=""/><span>veyra<span className="brand-ai">ai</span></span>{!compact&&<span className="version">0.3.3 <span className="sr-only">review candidate</span></span>}</span>;
}
