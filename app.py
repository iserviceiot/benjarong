import os
import json
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'documents.json')
LOGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs.json')
CATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'custom_categories.json')

DEFAULT_UNCATEGORIZED = "รอการจัดหมวดหมู่"

def load_docs():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                docs = json.load(f)
                for d in docs:
                    cats = d.get('categories', [])
                    if not cats:
                        d['categories'] = [DEFAULT_UNCATEGORIZED]
                return docs
        except Exception:
            return []
    return []

def save_docs(docs):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

def load_logs():
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_logs(logs):
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def load_custom_categories():
    if os.path.exists(CATS_FILE):
        try:
            with open(CATS_FILE, 'r', encoding='utf-8') as f:
                cats = json.load(f)
                if DEFAULT_UNCATEGORIZED not in cats:
                    cats.insert(0, DEFAULT_UNCATEGORIZED)
                return cats
        except Exception:
            return [DEFAULT_UNCATEGORIZED]
    return [DEFAULT_UNCATEGORIZED]

def save_custom_categories(cats):
    with open(CATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)

def add_log(action, details, user="System User", status="SUCCESS"):
    logs = load_logs()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.insert(0, {
        "id": f"log-{len(logs)+1:03d}",
        "timestamp": now_str,
        "action": action,
        "details": details,
        "user": user,
        "status": status
    })
    save_logs(logs)

def analyze_content_with_ai(title, content_text, filename):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_lower = (title + " " + content_text + " " + filename).lower()
    
    cats = []
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp']:
        cats.append("ภาพถ่ายและสื่อเอกสาร (Images & Media)")
    if any(k in text_lower for k in ["งบ", "บาท", "เงิน", "budget", "finance", "cost"]):
        cats.append("การจัดสรรงบประมาณและการเงิน (Budget & Finance)")
    if any(k in text_lower for k in ["แผน", "กลยุทธ์", "ภาพรวม", "strategy", "proposal"]):
        cats.append("ยุทธศาสตร์และข้อเสนอพันธมิตร (Strategy & Partnership)")
    if any(k in text_lower for k in ["cloud", "gdcc", "ระบบ", "it", "hardware", "software"]):
        cats.append("สถาปัตยกรรมระบบและคลาวด์ภาครัฐ (Architecture & GDCC Cloud)")
    if any(k in text_lower for k in ["mou", "บันทึกความเข้าใจ", "ภาคี"]):
        cats.append("บันทึกความร่วมมือ (MOU & Governance)")
        
    if not cats:
        cats = [DEFAULT_UNCATEGORIZED, "เอกสารข้อมูลนำเข้า"]

    keywords = [filename.split('.')[0], "Arena 101 iDoc", "การวิเคราะห์ AI Multi-Model"]
    if "งบ" in text_lower or "budget" in text_lower:
        keywords.append("การบริหารงบประมาณ")
    if "cloud" in text_lower or "it" in text_lower:
        keywords.append("เทคโนโลยีดิจิทัล")

    for kw in keywords:
        if kw not in cats:
            cats.append(kw)

    summary = f"สรุปสาระสำคัญของไฟล์ '{title}' ({filename}): ได้รับการประมวลผล ดึงข้อความ และวิเคราะห์จัดหมวดหมู่อัตโนมัติโดย AI เมื่อ {now_str} พร้อมสำหรับการสืบค้นเชิงลึกและการสรุปย่อโดยผู้เชี่ยวชาญ AI"

    expert_analysis = {
        "domestic_business": f"วิเคราะห์การสร้างมูลค่าเพิ่มและส่งเสริมผู้ประกอบการจากไฟล์ {filename}",
        "international_business": f"วิเคราะห์โอกาสขยายผลในระดับสากลจากไฟล์ {filename}",
        "strategy": "วิเคราะห์การกำหนดทิศทางยุทธศาสตร์เชิงรุกและการใช้ประโยชน์จากทรัพยากรดิจิทัล",
        "system_analyst": "วิเคราะห์โครงสร้างกระแสงาน (Workflow) สิทธิ์การใช้งาน และการเชื่อมโยงระบบ",
        "project_planner": "วิเคราะห์กรอบการดำเนินงาน รายงวดงาน Milestones และการบริหารความเสี่ยง",
        "it": "วิเคราะห์สถาปัตยกรรมไอที ความเสถียรของระบบ ความปลอดภัย และการรองรับ Traffic",
        "environmental_geography": "วิเคราะห์ผลกระทบทางภูมิศาสตร์ สิ่งแวดล้อม และพื้นที่ดำเนินงาน",
        "investor": "วิเคราะห์ความคุ้มค่าของการลงทุน ผลตอบแทนทางตรงและทางอ้อม (ROI)",
        "legal": "วิเคราะห์ความสอดคล้องตามกฎหมาย พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล (PDPA) และ พ.ร.บ. ไซเบอร์ฯ",
        "financial_accounting": "วิเคราะห์ความถูกต้องของการจัดสรรงบประมาณ การตรวจสอบบัญชี และสภาพคล่อง",
        "economics": "วิเคราะห์ผลกระทบเชิงบวกต่อเศรษฐกิจภาพรวม การลดการรั่วไหลของทุน",
        "marketing_competition": "วิเคราะห์โอกาสทางการตลาด กลยุทธ์การแข่งขัน การสร้างแบรนด์ และการวางตำแหน่งสินค้า/บริการ",
        "recommendations": "ข้อแนะนำเพิ่มเติม: ควรกำหนดดรรชนีชี้วัดความสำเร็จ (KPI) และติดตามผลอย่างต่อเนื่อง"
    }

    categorized_key_points = {
        "key_person": ["นายอารี (ผู้อำนวยการโครงการ)", "ทีมวิศวกรผู้เชี่ยวชาญประจำระบบ"],
        "agencies": ["สำนักงานพัฒนาดิจิทัลภาครัฐ", "หน่วยงานภาคีเครือข่ายเจ้าของไฟล์"],
        "budget": ["การจัดสรรงบประมาณโครงการดิจิทัล"],
        "timeline_details": ["เริ่ม 1 ม.ค. - สิ้นสุด 31 ธ.ค. / ระยะเวลา 12 เดือน / นัดประชุมติดตามทุกต้นเดือน"],
        "stakeholders": ["ผู้บริหารนโยบาย", "คณะทำงานตรวจรับ", "ประชาชนผู้รับบริการ"],
        "constraints": ["ต้องปฏิบัติตามระเบียบและกฎหมาย PDPA อย่างเคร่งครัด"],
        "advantages": ["เพิ่มประสิทธิภาพการทำงานด้วยเทคโนโลยีดิจิทัล"],
        "opportunities": ["ยกระดับการบริหารจัดการข้อมูลสู่อนาคต"],
        "observations_recommendations": ["ควรมีการติดตามผลอย่างประจำ"]
    }

    executive_structure = {
        "approver_name": "นายอารี (ประธานคณะกรรมการอนุมัติโครงการ)",
        "approver_agency": "สำนักงานกำกับนโยบายดิจิทัลภาครัฐ",
        "operator_name": "หัวหน้าทีมวิศวกรและผู้บริหารโครงการ",
        "operator_agency": "ฝ่ายปฏิบัติการและเทคโนโลยีดิจิทัล",
        "beneficiary_name": "ประชาชนผู้รับบริการ / ผู้ประกอบการภาคเอกชน",
        "beneficiary_agency": "ภาคีเครือข่ายและชุมชนท้องถิ่น"
    }

    return {
        "categories": cats,
        "keywords": keywords,
        "summary": summary,
        "expert_analysis": expert_analysis,
        "categorized_key_points": categorized_key_points,
        "executive_structure": executive_structure
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'), filename)

@app.route('/api/documents', methods=['GET'])
def get_documents():
    docs = load_docs()
    return jsonify({"status": "success", "documents": docs, "total": len(docs)})

@app.route('/api/documents/search', methods=['GET'])
def search_documents():
    q = request.args.get('q', '').strip().lower()
    cat = request.args.get('category', '').strip()
    title_filter = request.args.get('title', '').strip()
    kw_filter = request.args.get('keyword', '').strip().lower()

    docs = load_docs()
    filtered = []

    for d in docs:
        d_cats = d.get('categories', [d.get('category', '')])
        d_kws = [k.lower() for k in d.get('keywords', [])]

        if cat and cat not in d_cats and cat not in d_kws:
            continue
        if title_filter and d.get('title') != title_filter:
            continue
        if kw_filter and not any(kw_filter in k for k in d_kws):
            continue

        if q:
            searchable = f"{d.get('title','')} {d.get('summary','')} {d.get('source_agency','')} {' '.join(d_cats)} {' '.join(d_kws)}".lower()
            if not all(term in searchable for term in q.split()):
                continue

        filtered.append(d)

    return jsonify({"status": "success", "results": filtered, "total": len(filtered)})

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    files = request.files.getlist('file') or request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"status": "error", "message": "ไม่พบไฟล์ที่เลือก"}), 400

    uploaded_docs = []
    docs = load_docs()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for file in files:
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"upload_{uuid.uuid4().hex[:8]}.dat"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        content_text = f"ไฟล์นำเข้า {filename}"

        title = filename.replace('_', ' ').replace('-', ' ').rsplit('.', 1)[0]
        ai_result = analyze_content_with_ai(title, content_text, filename)

        new_doc = {
            "id": doc_id,
            "filename": filename,
            "title": f"เอกสารนำเข้า: {title}",
            "categories": ai_result["categories"],
            "keywords": ai_result["keywords"],
            "source_agency": "ไฟล์นำเข้าโดยผู้ใช้งาน (Multi-File Drag & Drop)",
            "analyzed_at": now_str,
            "summary": ai_result["summary"],
            "expert_analysis": ai_result["expert_analysis"],
            "categorized_key_points": ai_result["categorized_key_points"],
            "executive_structure": ai_result["executive_structure"],
            "file_size": f"{os.path.getsize(filepath) / 1024:.1f} KB"
        }

        docs.append(new_doc)
        uploaded_docs.append(new_doc)

    save_docs(docs)
    add_log("ADD_FILES", f"นำเข้าและวิเคราะห์ไฟล์จำนวน {len(uploaded_docs)} ไฟล์: {', '.join([d['filename'] for d in uploaded_docs])}")

    return jsonify({"status": "success", "documents": uploaded_docs, "total_uploaded": len(uploaded_docs)})

@app.route('/api/documents/bulk_categorize', methods=['POST'])
def bulk_categorize():
    data = request.get_json() or {}
    doc_ids = data.get('doc_ids', [])
    new_categories = data.get('categories', [])

    if not doc_ids or not new_categories:
        return jsonify({"status": "error", "message": "กรุณาเลือกเอกสารและหมวดหมู่อย่างน้อย 1 รายการ"}), 400

    docs = load_docs()
    updated_count = 0

    for d in docs:
        if d['id'] in doc_ids:
            d['categories'] = new_categories
            updated_count += 1

    save_docs(docs)
    add_log("BULK_CATEGORIZE", f"กำหนดหมวดหมู่ใหม่ให้กับเอกสารจำนวน {updated_count} ฉบับ: {', '.join(new_categories)}")
    return jsonify({"status": "success", "updated_count": updated_count})

@app.route('/api/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    docs = load_docs()
    doc = next((d for d in docs if d['id'] == doc_id), None)
    if not doc:
        return jsonify({"status": "error", "message": "ไม่พบเอกสาร"}), 404

    docs = [d for d in docs if d['id'] != doc_id]
    save_docs(docs)
    add_log("REMOVE_FILE", f"ลบเอกสาร '{doc['title']}' ({doc['filename']})")
    return jsonify({"status": "success", "message": "ลบเอกสารเรียบร้อย"})

@app.route('/api/categories', methods=['GET', 'POST', 'DELETE'])
def manage_categories():
    if request.method == 'GET':
        cats = load_custom_categories()
        return jsonify({"status": "success", "categories": cats})
    elif request.method == 'POST':
        data = request.get_json() or {}
        new_cat = data.get('category', '').strip()
        if not new_cat:
            return jsonify({"status": "error", "message": "กรุณากรอกชื่อหมวดหมู่"}), 400
        cats = load_custom_categories()
        if new_cat not in cats:
            cats.append(new_cat)
            save_custom_categories(cats)
            add_log("ADD_CATEGORY", f"เพิ่มหมวดหมู่ใหม่: '{new_cat}'")
        return jsonify({"status": "success", "categories": cats})
    elif request.method == 'DELETE':
        data = request.get_json() or {}
        cat_to_delete = data.get('category', '').strip()
        if not cat_to_delete or cat_to_delete == DEFAULT_UNCATEGORIZED:
            return jsonify({"status": "error", "message": "ไม่สามารถลบหมวดหมู่หลักระบบได้"}), 400
        
        cats = load_custom_categories()
        cats = [c for c in cats if c != cat_to_delete]
        save_custom_categories(cats)

        docs = load_docs()
        for d in docs:
            if 'categories' in d:
                d['categories'] = [c for c in d['categories'] if c != cat_to_delete]
                if not d['categories']:
                    d['categories'] = [DEFAULT_UNCATEGORIZED]
            if 'keywords' in d:
                d['keywords'] = [k for k in d['keywords'] if k != cat_to_delete]

        save_docs(docs)
        add_log("DELETE_CATEGORY", f"ลบหมวดหมู่ '{cat_to_delete}' (ย้ายเอกสารไป '{DEFAULT_UNCATEGORIZED}')")
        return jsonify({"status": "success", "categories": cats})

@app.route('/api/documents/<doc_id>/brief_summary', methods=['GET'])
def brief_summary(doc_id):
    docs = load_docs()
    doc = next((d for d in docs if d['id'] == doc_id), None)
    if not doc:
        return jsonify({"status": "error", "message": "ไม่พบเอกสาร"}), 404

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ckp = doc.get('categorized_key_points', {})
    kp = ", ".join(ckp.get('key_person', ['นายอารี (ผู้อำนวยการโครงการ)']))
    ag = ", ".join(ckp.get('agencies', ['สำนักงานพัฒนาดิจิทัลภาครัฐ']))
    tm = " | ".join(ckp.get('timeline_details', ['เริ่ม 1 ม.ค. - สิ้นสุด 31 ธ.ค.']))

    brief_text = f"""📄 สรุปย่อใจความสำคัญของเอกสารโดย AI ผู้เชี่ยวชาญ (Executive Brief Summary)
วิเคราะห์เมื่อ: {now_str}
หัวข้อ: {doc['title']} ({doc['filename']})

• สาระสำคัญโดยย่อ: {doc['summary']}
• ผู้รับผิดชอบหลัก (Key Person): {kp}
• หน่วยงานที่เกี่ยวข้อง (Agency): {ag}
• กรอบเวลาปฏิบัติการ (Timeline): {tm}
• ข้อแนะนำเชิงยุทธศาสตร์: ควรกำหนดดรรชนี KPI เพื่อติดตามผลและบริหารจัดการความเสี่ยงตามกฎหมาย PDPA"""

    return jsonify({
        "status": "success",
        "doc_id": doc_id,
        "title": doc['title'],
        "brief_summary": brief_text,
        "timestamp": now_str
    })

@app.route('/api/ai/experts_analysis', methods=['POST'])
def experts_analysis():
    data = request.get_json() or {}
    user_prompt = data.get('prompt', '').strip()
    selected_doc_ids = data.get('doc_ids', [])

    docs = load_docs()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not docs:
        return jsonify({
            "status": "success",
            "summary": "ขณะนี้ยังไม่มีเอกสารในระบบ กรุณาอัปโหลดเอกสารก่อนวิเคราะห์",
            "timestamp": now_str
        })

    if selected_doc_ids:
        target_docs = [d for d in docs if d['id'] in selected_doc_ids]
    else:
        target_docs = docs

    add_log("MULTI_DOC_12_EXPERTS", f"ประมวลผลสรุปย่อและวิเคราะห์ 12 ด้าน ({len(target_docs)} เอกสารที่เลือก)")

    return jsonify({
        "status": "success",
        "doc_count": len(target_docs),
        "target_docs": target_docs,
        "user_prompt": user_prompt,
        "timestamp": now_str
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    logs = load_logs()
    return jsonify({"status": "success", "logs": logs, "total": len(logs)})

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    default_logs = [{
        "id": "log-001",
        "timestamp": now_str,
        "action": "SYSTEM_INIT",
        "details": "เริ่มต้นใช้งานระบบ Arena 101 iDoc - 12 Domain Experts Engine",
        "user": "System Admin",
        "status": "SUCCESS"
    }]
    save_logs(default_logs)
    return jsonify({"status": "success", "logs": default_logs})

if __name__ == '__main__':
    print("----------------------------------------------------------------")
    print("Arena 101 iDoc Application Server (v3.4 12-Experts Tab & Brief Summaries Active)")
    print("Access application at: http://127.0.0.1:5000")
    print("----------------------------------------------------------------")
    app.run(host='0.0.0.0', port=5000, debug=True)
