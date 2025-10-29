// app.js — client-side helpers for product form
function randString(minLen){
	const chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
	const len = minLen + Math.floor(Math.random()* (Math.max(1,minLen)) );
	let out = '';
	for(let i=0;i<len;i++){ out += chars.charAt(Math.floor(Math.random()*chars.length)); }
	return out;
}

function generateSerial(){
	// Ensure at least 10 random chars after prefix
	const prefix = 'Shinyitem';
	const rand = randString(10);
	return prefix + rand;
}

function setPreviewField(id, value){
	const el = document.getElementById(id);
	if(!el) return;
	if(el.tagName.toLowerCase()==='a'){
		if(value){ el.textContent = value; el.href = value; }
		else { el.textContent='-'; el.removeAttribute('href'); }
	} else {
		el.textContent = value || '-';
	}
}

document.addEventListener('DOMContentLoaded', function(){
	// Elements
	const serialInput = document.getElementById('serial_no');
	const name = document.getElementById('name');
	const productCode = document.getElementById('product_code');
	const issueDate = document.getElementById('issue_date');
	const staffName = document.getElementById('staff_name');
	const staffId = document.getElementById('staff_id');
	const externalLink = document.getElementById('external_link');
	const certificate = document.getElementById('certificate');

	// Generate serial on load
	if(serialInput){ serialInput.value = generateSerial(); setPreviewField('pv_serial_no', serialInput.value); }

	// Sync function
	function syncAll(){
		setPreviewField('pv_name', name && name.value);
		setPreviewField('pv_product_code', productCode && productCode.value);
		setPreviewField('pv_issue_date', issueDate && issueDate.value);
		setPreviewField('pv_serial_no', serialInput && serialInput.value);
		setPreviewField('pv_staff_name', staffName && staffName.value);
		setPreviewField('pv_staff_id', staffId && staffId.value);
		setPreviewField('pv_external_link', externalLink && externalLink.value);
		// file name
		if(certificate && certificate.files && certificate.files.length>0){
			setPreviewField('pv_certificate', certificate.files[0].name);
		} else {
			setPreviewField('pv_certificate', null);
		}
	}

	// Add listeners
	[name, productCode, issueDate, staffName, staffId, externalLink].forEach(function(el){
		if(!el) return; el.addEventListener('input', syncAll);
	});
	if(certificate){ certificate.addEventListener('change', syncAll); }

	// If user wants a new serial (optional double-click)
	if(serialInput){
		serialInput.addEventListener('dblclick', function(){
			serialInput.value = generateSerial();
			syncAll();
		});
		// prevent editing since it's readonly
	}

	// Initial sync
	syncAll();
});
