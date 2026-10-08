import { chromium } from 'playwright'
const base='http://127.0.0.1:8000'
const b=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage']})
const p=await b.newPage({viewport:{width:1512,height:950}})
const errs=[]
p.on('console',m=>{if(m.type()==='error')errs.push('console: '+m.text().slice(0,200))})
p.on('pageerror',e=>errs.push('pageerror: '+e.message.slice(0,200)))
for (const [name,url,sel] of [
  ['QUEUE', `${base}/#/queue`, 'table tbody tr'],
  ['PLACES', `${base}/#/places?place=PL-AD002936`, 'text=Stored belief versions'],
  ['EVIDENCE', `${base}/#/evidence?address=AD002936`, 'text=Captured position'],
  ['REFUSAL', `${base}/#/resolve`, 'text=Not served'],
]) {
  console.log(`\n=== ${name} ===`)
  await p.goto(url,{waitUntil:'networkidle'})
  if (name==='REFUSAL') {
    const tabs = await p.locator('button').filter({hasText:'AD000002'}).count()
    console.log('  demo buttons matching AD000002:', tabs)
    await p.getByRole('button',{name:/AD000002/}).first().click()
  }
  await p.waitForTimeout(2500)
  const n = await p.locator(sel).count()
  console.log(`  selector "${sel}" → ${n}`)
  const txt = (await p.locator('body').innerText()).replace(/\s+/g,' ')
  console.log('  first 400 chars:', txt.slice(0,400))
}
console.log('\nERRORS:', errs.length ? errs : 'none')
await b.close()
