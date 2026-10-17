import {useEffect} from 'react';

// While a popup is open: move focus into it, keep Tab cycling inside it,
// close it on Escape, stop the page behind it from scrolling, and restore focus afterwards.
export function useDialogFocus(isOpen,onEscape,deps){
 useEffect(()=>{
  if(!isOpen)return;
  const previous=document.activeElement;
  const dialog=document.querySelector('[role=dialog]');
  const focusable=()=>Array.from(dialog?.querySelectorAll('button:not(:disabled),select,input,a[href]')||[]);
  focusable()[0]?.focus();
  const keydown=e=>{
   if(e.key==='Escape')onEscape();
   if(e.key==='Tab'){const elements=focusable();const first=elements[0],last=elements[elements.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}
  };
  document.addEventListener('keydown',keydown);const old=document.body.style.overflow;document.body.style.overflow='hidden';
  return()=>{document.removeEventListener('keydown',keydown);document.body.style.overflow=old;previous?.focus()};
 },deps);
}
