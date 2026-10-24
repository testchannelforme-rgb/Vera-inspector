/** Map displayed image content to remote viewport CSS pixels. DPR cancels out:
 * screenshots use scale:'css', DPR=1, and the image keeps its aspect ratio.
 * The measured rectangle must be the image itself, without borders/padding.
 */
export function toViewport(clientX, clientY, rect, viewport) {
  if(!rect.width || !rect.height) throw new Error('Preview has no dimensions.');
  const x=(clientX-rect.left)*viewport.width/rect.width;
  const y=(clientY-rect.top)*viewport.height/rect.height;
  return {x:Math.min(viewport.width-0.01,Math.max(0,x)),y:Math.min(viewport.height-0.01,Math.max(0,y))};
}
export function overlayStyle(box,viewport) {
  return {left:`${box.x/viewport.width*100}%`,top:`${box.y/viewport.height*100}%`,width:`${box.width/viewport.width*100}%`,height:`${box.height/viewport.height*100}%`};
}
