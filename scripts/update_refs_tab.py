"""Rewrite references tab with list view, search, and dual association management"""
import re
from pathlib import Path

path = str(Path(__file__).resolve().parent.parent / "templates" / "project.html")
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# 1. Replace references tab section (card grid → table list + search)
# ============================================================
old_refs_tab = '''            <!-- === 参考材料 Tab === -->
            <div v-else-if="tab === 'references'">
                <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem">
                    <h2 style="flex:1">参考材料</h2>
                    <button class="btn btn-ghost btn-sm" @click="openRefUrl">+ 添加链接</button>
                    <button class="btn btn-primary btn-sm" @click="openRefUpload">+ 上传文件</button>
                </div>
                <div v-if="references.length > 0" class="ref-grid">
                    <div v-for="ref in references" :key="ref.id" class="ref-card">
                        <div v-if="ref.file_path">
                            <img v-if="isImage(ref.file_path)" :src="'/uploads/' + ref.file_path" class="ref-thumb" @click="openRef(ref)">
                            <div v-else class="ref-file-icon" @click="openRef(ref)">&#128196;</div>
                        </div>
                        <div class="ref-link-icon" v-else-if="ref.url">&#128279;</div>
                        <div class="ref-name">[[ ref.title ]]</div>
                        <div class="ref-node text-muted" v-if="ref.nodes && ref.nodes.length > 0">关联: [[ ref.nodes.map(function(n){return n.name}).join(', ') ]]</div>
                        <div class="ref-notes text-muted" v-if="ref.notes">[[ ref.notes ]]</div>
                        <div class="ref-actions">
                            <button class="btn btn-ghost btn-sm" @click="openRef(ref)">[[ ref.file_path ? '查看文件' : '打开链接' ]]</button>
                            <button class="btn btn-ghost btn-sm" @click="deleteRef(ref)" style="color:var(--danger);margin-left:auto">&#10005;</button>
                        </div>
                    </div>
                </div>
                <div v-else class="empty-state" style="padding:3rem">
                    <div class="empty-icon">*</div>
                    <p>暂无参考材料</p>
                    <p class="text-muted">上传系统图、规格书等参考文件或添加外部链接</p>
                </div>
            </div>'''

new_refs_tab = '''            <!-- === 参考材料 Tab === -->
            <div v-else-if="tab === 'references'">
                <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem">
                    <h2 style="flex:1">参考材料</h2>
                    <input v-model="refSearchText" placeholder="搜索标题 / 类型 / 备注..." style="width:240px;font-size:.84rem" @input="refSearchDebounce">
                    <button class="btn btn-ghost btn-sm" @click="openRefUrl">+ 添加链接</button>
                    <button class="btn btn-primary btn-sm" @click="openRefUpload">+ 上传文件</button>
                </div>
                <div v-if="filteredRefList.length > 0" style="flex:1;overflow-y:auto;min-height:0">
                    <table class="func-table">
                        <thead><tr>
                            <th style="width:80px">类型</th>
                            <th style="min-width:200px">标题</th>
                            <th style="min-width:140px">关联结构节点</th>
                            <th style="min-width:140px">关联DFMEA</th>
                            <th style="min-width:100px">备注</th>
                            <th style="width:90px">操作</th>
                        </tr></thead>
                        <tbody>
                            <tr v-for="ref in filteredRefList" :key="ref.id">
                                <td><span class="tag" style="font-size:.72rem;background:var(--accent-muted);color:var(--accent);cursor:default">[[ ref.type ]]</span></td>
                                <td>
                                    <a v-if="ref.file_path" :href="'/uploads/' + ref.file_path" target="_blank" style="font-weight:550">[[ ref.title ]]</a>
                                    <a v-else-if="ref.url" :href="ref.url" target="_blank" style="font-weight:550">[[ ref.title ]]</a>
                                    <span v-else style="font-weight:550">[[ ref.title ]]</span>
                                </td>
                                <td>
                                    <span v-if="ref.nodes && ref.nodes.length > 0" style="display:flex;flex-wrap:wrap;gap:.2rem">
                                        <span v-for="n in ref.nodes" :key="'rn'+n.id" class="tag" style="font-size:.68rem;background:var(--canvas);color:var(--text-secondary);cursor:default" :title="n.name">[[ n.name ]]</span>
                                    </span>
                                    <span v-else class="text-muted" style="font-size:.75rem">-</span>
                                </td>
                                <td>
                                    <span v-if="ref.failure_modes && ref.failure_modes.length > 0" style="display:flex;flex-wrap:wrap;gap:.2rem">
                                        <span v-for="fm in ref.failure_modes" :key="'rf'+fm.id" class="tag" style="font-size:.68rem;background:var(--canvas);color:var(--text-secondary);cursor:default" :title="fm.mode_desc">[[ fm.node_name ]]</span>
                                    </span>
                                    <span v-else class="text-muted" style="font-size:.75rem">-</span>
                                </td>
                                <td class="text-muted" style="font-size:.78rem">[[ ref.notes || '-' ]]</td>
                                <td class="nowrap">
                                    <button class="btn btn-ghost btn-sm" @click="openRefAssoc(ref)" title="编辑关联" style="font-size:.7rem">&#128279;</button>
                                    <button class="btn btn-ghost btn-sm" @click="openRef(ref)" title="查看">&#128065;</button>
                                    <button class="btn btn-ghost btn-sm" @click="deleteRef(ref)" title="删除" style="color:var(--danger)">&#10005;</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div v-else class="empty-state" style="padding:3rem">
                    <div class="empty-icon">*</div>
                    <p v-if="references.length === 0">暂无参考材料</p>
                    <p v-else>无匹配结果</p>
                    <p class="text-muted">上传系统图、规格书等参考文件或添加外部链接</p>
                </div>
            </div>'''

if old_refs_tab in content:
    content = content.replace(old_refs_tab, new_refs_tab)
    print("OK: references tab replaced")
else:
    print("FAIL: references tab not found")

# ============================================================
# 2. Update upload modal — add failure mode checkboxes
# ============================================================
old_upload_modal_end = '''            <div class="form-group"><label>备注</label><input v-model="refForm.notes" placeholder="补充说明"></div>
            <div class="modal-actions">
                <button class="btn btn-ghost" @click="showRefUpload = false">取消</button>
                <button class="btn btn-primary" @click="uploadRef" :disabled="!refForm.title.trim() || !selectedFile">上传</button>
            </div>
        </div>
    </div>

    <!-- === 添加链接弹窗 === -->'''

new_upload_modal_end = '''            <div class="form-group"><label>备注</label><input v-model="refForm.notes" placeholder="补充说明"></div>
            <div class="form-group">
                <label>关联DFMEA失效模式 <span class="text-muted" style="font-weight:400">（[[ refSelFmIds.length ]] 项已选）</span></label>
                <input type="text" v-model="refFmSearch" placeholder="输入关键词搜索失效模式..." style="width:100%;font-size:.8rem;margin-bottom:.25rem">
                <div v-if="refFmFiltered.length > 0" style="max-height:160px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius)">
                    <label v-for="fm in refFmFiltered" :key="fm.id" style="display:flex;align-items:center;gap:.35rem;padding:.2rem .5rem;font-size:.78rem;cursor:pointer;border-bottom:1px dotted var(--border)">
                        <input type="checkbox" :value="fm.id" v-model="refSelFmIds" style="width:auto;flex-shrink:0">
                        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">[[ fm.mode_desc ]]</span>
                        <span style="font-size:.68rem;color:var(--text-muted);flex-shrink:0">[[ fm.node_name ]]</span>
                    </label>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-ghost" @click="showRefUpload = false">取消</button>
                <button class="btn btn-primary" @click="uploadRef" :disabled="!refForm.title.trim() || !selectedFile">上传</button>
            </div>
        </div>
    </div>

    <!-- === 添加链接弹窗 === -->'''

if old_upload_modal_end in content:
    content = content.replace(old_upload_modal_end, new_upload_modal_end)
    print("OK: upload modal updated")
else:
    print("FAIL: upload modal end not found")

# ============================================================
# 3. Update link modal — add failure mode checkboxes
# ============================================================
old_link_modal_end = '''            <div class="form-group"><label>备注</label><input v-model="refForm.notes" placeholder="补充说明"></div>
            <div class="modal-actions">
                <button class="btn btn-ghost" @click="showRefUrl = false">取消</button>
                <button class="btn btn-primary" @click="saveRefUrl" :disabled="!refForm.title.trim() || !refForm.url.trim()">保存</button>
            </div>
        </div>
    </div>

</div>'''

new_link_modal_end = '''            <div class="form-group"><label>备注</label><input v-model="refForm.notes" placeholder="补充说明"></div>
            <div class="form-group">
                <label>关联DFMEA失效模式 <span class="text-muted" style="font-weight:400">（[[ refSelFmIds.length ]] 项已选）</span></label>
                <input type="text" v-model="refFmSearch" placeholder="输入关键词搜索失效模式..." style="width:100%;font-size:.8rem;margin-bottom:.25rem">
                <div v-if="refFmFiltered.length > 0" style="max-height:160px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius)">
                    <label v-for="fm in refFmFiltered" :key="fm.id" style="display:flex;align-items:center;gap:.35rem;padding:.2rem .5rem;font-size:.78rem;cursor:pointer;border-bottom:1px dotted var(--border)">
                        <input type="checkbox" :value="fm.id" v-model="refSelFmIds" style="width:auto;flex-shrink:0">
                        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">[[ fm.mode_desc ]]</span>
                        <span style="font-size:.68rem;color:var(--text-muted);flex-shrink:0">[[ fm.node_name ]]</span>
                    </label>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-ghost" @click="showRefUrl = false">取消</button>
                <button class="btn btn-primary" @click="saveRefUrl" :disabled="!refForm.title.trim() || !refForm.url.trim()">保存</button>
            </div>
        </div>
    </div>

    <!-- === 参考资料关联编辑弹窗 === -->
    <div v-if="showRefAssoc" class="modal-overlay">
        <div class="modal" style="max-width:680px;min-width:520px">
            <h2>编辑关联 — [[ editingRefAssoc ? editingRefAssoc.title : '' ]]</h2>
            <div style="display:flex;gap:1rem">
                <div style="flex:1;min-width:0">
                    <label style="font-weight:600;font-size:.84rem;display:block;margin-bottom:.4rem">关联结构节点 <span class="text-muted" style="font-weight:400">（[[ refAssocNodeIds.length ]] 项）</span></label>
                    <input type="text" v-model="refAssocNodeSearch" placeholder="搜索节点..." style="width:100%;font-size:.8rem;margin-bottom:.3rem">
                    <div style="max-height:260px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius)">
                        <label v-for="n in refAssocNodeFiltered" :key="'an'+n.id" style="display:flex;align-items:center;gap:.35rem;padding:.2rem .5rem;font-size:.78rem;cursor:pointer;border-bottom:1px dotted var(--border)">
                            <input type="checkbox" :value="n.id" v-model="refAssocNodeIds" style="width:auto;flex-shrink:0">
                            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">[[ n.name ]]</span>
                        </label>
                    </div>
                </div>
                <div style="flex:1;min-width:0">
                    <label style="font-weight:600;font-size:.84rem;display:block;margin-bottom:.4rem">关联DFMEA失效模式 <span class="text-muted" style="font-weight:400">（[[ refAssocFmIds.length ]] 项）</span></label>
                    <input type="text" v-model="refAssocFmSearch" placeholder="搜索失效模式..." style="width:100%;font-size:.8rem;margin-bottom:.3rem">
                    <div style="max-height:260px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius)">
                        <label v-for="fm in refAssocFmFiltered" :key="'af'+fm.id" style="display:flex;align-items:center;gap:.35rem;padding:.2rem .5rem;font-size:.78rem;cursor:pointer;border-bottom:1px dotted var(--border)">
                            <input type="checkbox" :value="fm.id" v-model="refAssocFmIds" style="width:auto;flex-shrink:0">
                            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">[[ fm.mode_desc ]]</span>
                            <span style="font-size:.68rem;color:var(--text-muted);flex-shrink:0">[[ fm.node_name ]]</span>
                        </label>
                    </div>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-ghost" @click="showRefAssoc = false">取消</button>
                <button class="btn btn-primary" @click="saveRefAssoc">保存关联</button>
            </div>
        </div>
    </div>

</div>'''

if old_link_modal_end in content:
    content = content.replace(old_link_modal_end, new_link_modal_end)
    print("OK: link modal updated + assoc modal added")
else:
    print("FAIL: link modal end not found")

# ============================================================
# 4. Update JS — add new refs for FM association + search
# ============================================================

# Add ref variables after existing refs
old_ref_vars = "        var refSelNodeIds = ref([]);\n        var refNodeSearch = ref('');"
new_ref_vars = '''        var refSelNodeIds = ref([]);
        var refSelFmIds = ref([]);
        var refFmSearch = ref('');
        var allFmFlat = ref([]);
        var refNodeSearch = ref('');
        var refSearchText = ref('');
        var refSearchDebounce = debounce(function () {}, 200);
        var showRefAssoc = ref(false);
        var editingRefAssoc = ref(null);
        var refAssocNodeIds = ref([]);
        var refAssocFmIds = ref([]);
        var refAssocNodeSearch = ref('');
        var refAssocFmSearch = ref('');'''

if old_ref_vars in content:
    content = content.replace(old_ref_vars, new_ref_vars)
    print("OK: JS ref vars added")
else:
    print("FAIL: JS ref vars not found")

# Add computed for filtered references
old_ref_filtered = "        var refNodeFiltered = computed(function () {"
new_ref_filtered = '''        var refFmFiltered = computed(function () {
            var q = refFmSearch.value.toLowerCase().trim();
            if (!q) return [];
            return allFmFlat.value.filter(function (fm) { return fm.mode_desc.toLowerCase().includes(q) || fm.node_name.toLowerCase().includes(q); }).slice(0, 30);
        });
        var filteredRefList = computed(function () {
            var q = refSearchText.value.toLowerCase().trim();
            if (!q) return references.value;
            return references.value.filter(function (r) {
                return r.title.toLowerCase().includes(q) || (r.type || '').includes(q) || (r.notes || '').toLowerCase().includes(q);
            });
        });
        var refAssocNodeFiltered = computed(function () {
            var q = refAssocNodeSearch.value.toLowerCase().trim();
            if (!q) return allNodesFlat.value.slice(0, 30);
            return allNodesFlat.value.filter(function (n) { return n.name.toLowerCase().includes(q); }).slice(0, 30);
        });
        var refAssocFmFiltered = computed(function () {
            var q = refAssocFmSearch.value.toLowerCase().trim();
            if (!q) return allFmFlat.value.slice(0, 30);
            return allFmFlat.value.filter(function (fm) { return fm.mode_desc.toLowerCase().includes(q) || fm.node_name.toLowerCase().includes(q); }).slice(0, 30);
        });
        var refNodeFiltered = computed(function () {'''

if old_ref_filtered in content:
    content = content.replace(old_ref_filtered, new_ref_filtered)
    print("OK: filtered computed added")
else:
    print("FAIL: ref filtered not found")

# Update loadAllNodesFlat to also load failure modes
old_load_all_nodes = "        function loadAllNodesFlat() { API.get('/api/v1/projects/' + PROJECT_ID + '/structure').then(function (t) { var flat = []; function collect(ns) { for (var i = 0; i < ns.length; i++) { flat.push({ id: ns[i].id, name: ns[i].name }); if (ns[i].children) collect(ns[i].children); } } collect(t); allNodesFlat.value = flat; }).catch(function () { allNodesFlat.value = []; }); }"
new_load_all_nodes = '''        function loadAllNodesFlat() { API.get('/api/v1/projects/' + PROJECT_ID + '/structure').then(function (t) { var flat = []; function collect(ns) { for (var i = 0; i < ns.length; i++) { flat.push({ id: ns[i].id, name: ns[i].name }); if (ns[i].children) collect(ns[i].children); } } collect(t); allNodesFlat.value = flat; }).catch(function () { allNodesFlat.value = []; }); }
        function loadAllFmFlat() { API.get('/api/v1/projects/' + PROJECT_ID + '/failures/all').then(function (d) { allFmFlat.value = d; }).catch(function () { allFmFlat.value = []; }); }'''

if old_load_all_nodes in content:
    content = content.replace(old_load_all_nodes, new_load_all_nodes)
    print("OK: loadAllFmFlat added")
else:
    print("FAIL: loadAllNodesFlat not found")

# Update openRefUpload to also load all FM and reset FM ids
old_open_ref_upload = "        function openRefUpload() { Object.assign(refForm, { title: '', type: '其他', url: '', notes: '' }); refSelNodeIds.value = []; refNodeSearch.value = ''; selectedFile.value = null; showRefUpload.value = true; }"
new_open_ref_upload = "        function openRefUpload() { Object.assign(refForm, { title: '', type: '其他', url: '', notes: '' }); refSelNodeIds.value = []; refSelFmIds.value = []; refFmSearch.value = ''; refNodeSearch.value = ''; selectedFile.value = null; loadAllFmFlat(); showRefUpload.value = true; }"

if old_open_ref_upload in content:
    content = content.replace(old_open_ref_upload, new_open_ref_upload)
    print("OK: openRefUpload updated")
else:
    print("FAIL: openRefUpload not found")

# Update openRefUrl similarly
old_open_ref_url = "        function openRefUrl() { Object.assign(refForm, { title: '', type: '其他', url: '', notes: '' }); refSelNodeIds.value = []; refNodeSearch.value = ''; selectedFile.value = null; showRefUrl.value = true; }"
new_open_ref_url = "        function openRefUrl() { Object.assign(refForm, { title: '', type: '其他', url: '', notes: '' }); refSelNodeIds.value = []; refSelFmIds.value = []; refFmSearch.value = ''; refNodeSearch.value = ''; selectedFile.value = null; loadAllFmFlat(); showRefUrl.value = true; }"

if old_open_ref_url in content:
    content = content.replace(old_open_ref_url, new_open_ref_url)
    print("OK: openRefUrl updated")
else:
    print("FAIL: openRefUrl not found")

# Update uploadRef to include failure_mode_ids
old_upload_ref = """        function uploadRef() { if (!selectedFile.value) return; var fd = new FormData(); fd.append('file', selectedFile.value); fd.append('title', refForm.title.trim()); fd.append('type', refForm.type); fd.append('node_ids', JSON.stringify(refSelNodeIds.value)); fd.append('notes', refForm.notes); fetch('/api/v1/projects/' + PROJECT_ID + '/references/upload', { method: 'POST', body: fd }).then(function (res) { if (!res.ok) throw new Error('上传失败'); showRefUpload.value = false; loadReferences(); showToast('已上传', 'success'); }).catch(function (e) { showToast('上传失败: ' + e.message, 'warning'); }); }"""
new_upload_ref = """        function uploadRef() { if (!selectedFile.value) return; var fd = new FormData(); fd.append('file', selectedFile.value); fd.append('title', refForm.title.trim()); fd.append('type', refForm.type); fd.append('node_ids', JSON.stringify(refSelNodeIds.value)); fd.append('failure_mode_ids', JSON.stringify(refSelFmIds.value)); fd.append('notes', refForm.notes); fetch('/api/v1/projects/' + PROJECT_ID + '/references/upload', { method: 'POST', body: fd }).then(function (res) { if (!res.ok) throw new Error('上传失败'); showRefUpload.value = false; loadReferences(); showToast('已上传', 'success'); }).catch(function (e) { showToast('上传失败: ' + e.message, 'warning'); }); }"""

if old_upload_ref in content:
    content = content.replace(old_upload_ref, new_upload_ref)
    print("OK: uploadRef updated")
else:
    print("FAIL: uploadRef not found")

# Update saveRefUrl to include failure_mode_ids
old_save_ref_url = """        function saveRefUrl() { API.post('/api/v1/projects/' + PROJECT_ID + '/references', { title: refForm.title.trim(), type: refForm.type, node_ids: refSelNodeIds.value.slice(), url: refForm.url.trim(), notes: refForm.notes }).then(function () { showRefUrl.value = false; loadReferences(); showToast('已添加', 'success'); }).catch(function (e) { showToast('保存失败: ' + e.message, 'warning'); }); }"""
new_save_ref_url = """        function saveRefUrl() { API.post('/api/v1/projects/' + PROJECT_ID + '/references', { title: refForm.title.trim(), type: refForm.type, node_ids: refSelNodeIds.value.slice(), failure_mode_ids: refSelFmIds.value.slice(), url: refForm.url.trim(), notes: refForm.notes }).then(function () { showRefUrl.value = false; loadReferences(); showToast('已添加', 'success'); }).catch(function (e) { showToast('保存失败: ' + e.message, 'warning'); }); }"""

if old_save_ref_url in content:
    content = content.replace(old_save_ref_url, new_save_ref_url)
    print("OK: saveRefUrl updated")
else:
    print("FAIL: saveRefUrl not found")

# Add openRefAssoc and saveRefAssoc functions before the loadReferences function
old_load_refs_func = "        function loadReferences() { API.get('/api/v1/projects/' + PROJECT_ID + '/references').then(function (d) { references.value = d; }).catch(function () { references.value = []; }); }"
new_load_refs_func = """        function openRefAssoc(ref) {
            editingRefAssoc.value = ref;
            refAssocNodeIds.value = (ref.nodes || []).map(function (n) { return n.id; });
            refAssocFmIds.value = (ref.failure_modes || []).map(function (fm) { return fm.id; });
            refAssocNodeSearch.value = '';
            refAssocFmSearch.value = '';
            loadAllNodesFlat();
            loadAllFmFlat();
            showRefAssoc.value = true;
        }
        function saveRefAssoc() {
            if (!editingRefAssoc.value) return;
            API.put('/api/v1/references/' + editingRefAssoc.value.id, { node_ids: refAssocNodeIds.value.slice(), failure_mode_ids: refAssocFmIds.value.slice() }).then(function () {
                showRefAssoc.value = false;
                loadReferences();
                showToast('关联已更新', 'success');
            }).catch(function (e) { showToast('保存失败: ' + e.message, 'warning'); });
        }
        function loadReferences() { API.get('/api/v1/projects/' + PROJECT_ID + '/references').then(function (d) { references.value = d; }).catch(function () { references.value = []; }); }"""

if old_load_refs_func in content:
    content = content.replace(old_load_refs_func, new_load_refs_func)
    print("OK: loadReferences + assoc functions updated")
else:
    print("FAIL: loadReferences not found")

# Update the tab watcher to load all FM flat when switching to references tab
old_tab_watcher = "            if (tab === 'references') { loadReferences(); loadAllNodesFlat(); }"
new_tab_watcher = "            if (tab === 'references') { loadReferences(); loadAllNodesFlat(); loadAllFmFlat(); }"

if old_tab_watcher in content:
    content = content.replace(old_tab_watcher, new_tab_watcher)
    print("OK: tab watcher updated")
else:
    # Try alternative format
    alt_old = "            if (val === 'references') { loadReferences(); loadAllNodesFlat(); }"
    alt_new = "            if (val === 'references') { loadReferences(); loadAllNodesFlat(); loadAllFmFlat(); }"
    if alt_old in content:
        content = content.replace(alt_old, alt_new)
        print("OK: tab watcher updated (alt)")
    else:
        print("FAIL: tab watcher not found")

# Update refSearchDebounce to actually filter
old_debounce = "        var refSearchDebounce = debounce(function () {}, 200);"
new_debounce = "        var refSearchDebounce = debounce(function () { refSearchText.value = refSearchText.value; }, 200);"

# Actually, the debounce doesn't matter since filteredRefList is a computed that depends on refSearchText
# The v-model already binds to refSearchText. Let me just remove the refSearchDebounce complexity
# and keep it simple.
if old_debounce in content:
    content = content.replace(old_debounce, "        var refSearchDebounce = debounce(function () {}, 150);")
    print("OK: debounce simplified")

# Add return object entries for new vars
old_return_refs = "            references: references, showRefUpload: showRefUpload, showRefUrl: showRefUrl,"
new_return_refs = """            references: references, showRefUpload: showRefUpload, showRefUrl: showRefUrl,
            showRefAssoc: showRefAssoc, editingRefAssoc: editingRefAssoc,
            openRefAssoc: openRefAssoc, saveRefAssoc: saveRefAssoc,
            refAssocNodeIds: refAssocNodeIds, refAssocFmIds: refAssocFmIds,
            refAssocNodeSearch: refAssocNodeSearch, refAssocFmSearch: refAssocFmSearch,
            refAssocNodeFiltered: refAssocNodeFiltered, refAssocFmFiltered: refAssocFmFiltered,
            refSelFmIds: refSelFmIds, refFmSearch: refFmSearch, refFmFiltered: refFmFiltered,
            refSearchText: refSearchText, refSearchDebounce: refSearchDebounce,
            filteredRefList: filteredRefList, allFmFlat: allFmFlat,
            loadAllFmFlat: loadAllFmFlat,"""

if old_return_refs in content:
    content = content.replace(old_return_refs, new_return_refs)
    print("OK: return object updated with new refs")
else:
    print("FAIL: return refs not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nAll done!")
