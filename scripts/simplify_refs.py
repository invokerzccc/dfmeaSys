"""Simplify references tab: type filters, no associations, merged add button"""
from pathlib import Path

path = str(Path(__file__).resolve().parent.parent / "templates" / "project.html")
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# 1. Replace references tab — simplified list with type filters
# ============================================================
old_refs = '''            <!-- === 参考材料 Tab === -->
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

new_refs = '''            <!-- === 参考材料 Tab === -->
            <div v-else-if="tab === 'references'">
                <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem">
                    <h2 style="flex:1">参考材料</h2>
                    <input v-model="refSearchText" placeholder="搜索标题或备注..." style="width:200px;font-size:.84rem">
                    <button class="btn btn-primary btn-sm" @click="openRefAdd">+ 添加</button>
                </div>
                <div style="display:flex;gap:.3rem;margin-bottom:.75rem;flex-wrap:wrap">
                    <button v-for="t in refTypeTabs" :key="t.value" class="btn btn-sm"
                        :class="refTypeFilter === t.value ? 'btn-primary' : 'btn-ghost'"
                        @click="refTypeFilter = t.value" style="font-size:.78rem">[[ t.label ]] ([[ refTypeCount(t.value) ]])</button>
                </div>
                <div v-if="filteredRefList.length > 0" style="flex:1;overflow-y:auto;min-height:0">
                    <table class="func-table">
                        <thead><tr>
                            <th style="width:80px">类型</th>
                            <th style="min-width:240px">标题</th>
                            <th style="min-width:120px">备注</th>
                            <th style="width:80px">操作</th>
                        </tr></thead>
                        <tbody>
                            <tr v-for="ref in filteredRefList" :key="ref.id">
                                <td><span class="tag" :style="{ fontSize: '.72rem', background: refTypeColor(ref.type), color: '#fff' }">[[ ref.type ]]</span></td>
                                <td>
                                    <a v-if="ref.file_path" :href="'/uploads/' + ref.file_path" target="_blank" style="font-weight:550">[[ ref.title ]]</a>
                                    <a v-else-if="ref.url" :href="ref.url" target="_blank" style="font-weight:550">[[ ref.title ]]</a>
                                    <span v-else style="font-weight:550">[[ ref.title ]]</span>
                                </td>
                                <td class="text-muted" style="font-size:.78rem">[[ ref.notes || '-' ]]</td>
                                <td class="nowrap">
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
                    <p class="text-muted">点击"+ 添加"上传文件或添加链接</p>
                </div>
            </div>'''

if old_refs in content:
    content = content.replace(old_refs, new_refs)
    print("OK: references tab replaced")
else:
    print("FAIL: old refs tab not found")

# ============================================================
# 2. Replace upload modal — unified add (file or URL or both)
# ============================================================
old_upload = '''    <!-- === 上传文件弹窗 === -->
    <div v-if="showRefUpload" class="modal-overlay">
        <div class="modal" style="max-width:520px">
            <h2>上传参考文件</h2>
            <div class="form-group"><label>标题 <span style="color:var(--danger)">*</span></label><input v-model="refForm.title" placeholder="材料名称"></div>
            <div class="form-group">
                <label>关联节点 <span class="text-muted" style="font-weight:400">（[[ refSelNodeIds.length ]] 项已选）</span></label>
                <div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.35rem" v-if="refSelNodeIds.length > 0">
                    <span v-for="nid in refSelNodeIds" :key="nid" class="tag" style="font-size:.75rem;cursor:pointer;background:var(--accent);color:#fff;display:inline-flex;align-items:center;gap:.3rem"
                        @click="refSelNodeIds = refSelNodeIds.filter(function(id){return id !== nid})">
                        [[ refNodeName(nid) ]] <span style="opacity:.7;font-weight:700">&times;</span>
                    </span>
                </div>
                <input type="text" v-model="refNodeSearch" placeholder="输入关键词搜索节点..." style="width:100%;font-size:.8rem;margin-bottom:.25rem">
                <div v-if="refNodeFiltered.length > 0" style="max-height:160px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius)">
                    <label v-for="n in refNodeFiltered" :key="n.id" style="display:flex;align-items:center;gap:.35rem;padding:.2rem .5rem;font-size:.78rem;cursor:pointer;border-bottom:1px dotted var(--border)">
                        <input type="checkbox" :value="n.id" v-model="refSelNodeIds" style="width:auto;flex-shrink:0">
                        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">[[ n.name ]]</span>
                    </label>
                </div>
            </div>
            <div class="form-group"><label>文件 <span style="color:var(--danger)">*</span></label><input type="file" ref="fileInput" @change="onFileSelected" style="border:none;padding:.3rem 0">
                <div v-if="selectedFile" class="text-muted" style="font-size:.8rem;margin-top:.2rem">[[ selectedFile.name ]] ([[ (selectedFile.size / 1024).toFixed(1) ]] KB)</div>
            </div>
            <div class="form-group"><label>备注</label><input v-model="refForm.notes" placeholder="补充说明"></div>
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
    </div>'''

new_upload = '''    <!-- === 添加参考材料弹窗 === -->
    <div v-if="showRefAdd" class="modal-overlay">
        <div class="modal" style="max-width:520px">
            <h2>添加参考材料</h2>
            <div class="form-group"><label>标题 <span style="color:var(--danger)">*</span></label><input v-model="refForm.title" placeholder="材料名称"></div>
            <div class="form-group">
                <label>类型</label>
                <select v-model="refForm.type"><option value="链接">链接</option><option value="文档">文档</option><option value="图片">图片</option><option value="其他">其他</option></select>
            </div>
            <div class="form-group" v-if="refForm.type === '链接'">
                <label>URL <span style="color:var(--danger)">*</span></label>
                <input v-model="refForm.url" placeholder="https://...">
            </div>
            <div class="form-group" v-else>
                <label>文件 <span v-if="!editingRefAdd" style="color:var(--danger)">*</span></label>
                <input type="file" ref="fileInput" @change="onFileSelected" style="border:none;padding:.3rem 0">
                <div v-if="selectedFile" class="text-muted" style="font-size:.8rem;margin-top:.2rem">[[ selectedFile.name ]] ([[ (selectedFile.size / 1024).toFixed(1) ]] KB)</div>
            </div>
            <div class="form-group"><label>备注</label><input v-model="refForm.notes" placeholder="补充说明"></div>
            <div class="modal-actions">
                <button class="btn btn-ghost" @click="showRefAdd = false">取消</button>
                <button class="btn btn-primary" @click="saveRef" :disabled="!refForm.title.trim() || (refForm.type !== '链接' && !selectedFile) || (refForm.type === '链接' && !refForm.url.trim())">保存</button>
            </div>
        </div>
    </div>'''

if old_upload in content:
    content = content.replace(old_upload, new_upload)
    print("OK: upload modal replaced with unified add")
else:
    print("FAIL: upload modal not found")

# ============================================================
# 3. Remove old link modal and assoc modal
# ============================================================
old_link_modal = '''    <!-- === 添加链接弹窗 === -->
    <div v-if="showRefUrl" class="modal-overlay">
        <div class="modal" style="max-width:520px">
            <h2>添加参考链接</h2>
            <div class="form-group"><label>标题 <span style="color:var(--danger)">*</span></label><input v-model="refForm.title" placeholder="链接名称"></div>
            <div class="form-group">
                <label>关联节点 <span class="text-muted" style="font-weight:400">（[[ refSelNodeIds.length ]] 项已选）</span></label>
                <div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.35rem" v-if="refSelNodeIds.length > 0">
                    <span v-for="nid in refSelNodeIds" :key="nid" class="tag" style="font-size:.75rem;cursor:pointer;background:var(--accent);color:#fff;display:inline-flex;align-items:center;gap:.3rem"
                        @click="refSelNodeIds = refSelNodeIds.filter(function(id){return id !== nid})">
                        [[ refNodeName(nid) ]] <span style="opacity:.7;font-weight:700">&times;</span>
                    </span>
                </div>
                <input type="text" v-model="refNodeSearch" placeholder="输入关键词搜索节点..." style="width:100%;font-size:.8rem;margin-bottom:.25rem">
                <div v-if="refNodeFiltered.length > 0" style="max-height:160px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius)">
                    <label v-for="n in refNodeFiltered" :key="n.id" style="display:flex;align-items:center;gap:.35rem;padding:.2rem .5rem;font-size:.78rem;cursor:pointer;border-bottom:1px dotted var(--border)">
                        <input type="checkbox" :value="n.id" v-model="refSelNodeIds" style="width:auto;flex-shrink:0">
                        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">[[ n.name ]]</span>
                    </label>
                </div>
            </div>
            <div class="form-group"><label>URL <span style="color:var(--danger)">*</span></label><input v-model="refForm.url" placeholder="https://..."></div>
            <div class="form-group"><label>备注</label><input v-model="refForm.notes" placeholder="补充说明"></div>
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
    </div>'''

# Remove both old link modal and old assoc modal
if old_link_modal in content:
    content = content.replace(old_link_modal, '')
    print("OK: old link modal + assoc modal removed")
else:
    print("FAIL: old link modal not found")

# ============================================================
# 4. JS: Replace ref-related vars and functions
# ============================================================

# Remove complex ref vars, replace with simple ones
old_ref_vars = '''        var refSelNodeIds = ref([]);
        var refSelFmIds = ref([]);
        var refFmSearch = ref('');
        var allFmFlat = ref([]);
        var refNodeSearch = ref('');
        var refSearchText = ref('');
        var refSearchDebounce = debounce(function () {}, 150);
        var showRefAssoc = ref(false);
        var editingRefAssoc = ref(null);
        var refAssocNodeIds = ref([]);
        var refAssocFmIds = ref([]);
        var refAssocNodeSearch = ref('');
        var refAssocFmSearch = ref('');'''

new_ref_vars = '''        var refSearchText = ref('');
        var refTypeFilter = ref('全部');
        var refTypeTabs = [{ value: '全部', label: '全部' }, { value: '链接', label: '链接' }, { value: '文档', label: '文档' }, { value: '图片', label: '图片' }, { value: '其他', label: '其他' }];
        var refNodeSearch = ref('');
        var refSelNodeIds = ref([]);
        var showRefAdd = ref(false);
        var editingRefAdd = ref(false);'''

if old_ref_vars in content:
    content = content.replace(old_ref_vars, new_ref_vars)
    print("OK: JS ref vars simplified")
else:
    print("FAIL: JS ref vars not found")

# Replace the big block of ref-related computeds with simple ones
old_ref_filtered = '''        var refFmFiltered = computed(function () {
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

new_ref_filtered = '''        var filteredRefList = computed(function () {
            var q = refSearchText.value.toLowerCase().trim();
            var list = references.value;
            if (q) list = list.filter(function (r) { return r.title.toLowerCase().includes(q) || (r.notes || '').toLowerCase().includes(q); });
            if (refTypeFilter.value !== '全部') list = list.filter(function (r) { return r.type === refTypeFilter.value; });
            return list;
        });
        function refTypeCount(type) { if (type === '全部') return references.value.length; return references.value.filter(function (r) { return r.type === type; }).length; }
        function refTypeColor(type) { var m = { '链接': 'var(--accent)', '文档': 'var(--warning)', '图片': 'var(--success)', '其他': 'var(--text-muted)' }; return m[type] || 'var(--text-muted)'; }
        var refNodeFiltered = computed(function () {'''

if old_ref_filtered in content:
    content = content.replace(old_ref_filtered, new_ref_filtered)
    print("OK: filtered computed simplified")
else:
    print("FAIL: ref filtered not found")

# Remove allFmFlat related functions
old_load_all_fm = '''        function loadAllFmFlat() { API.get('/api/v1/projects/' + PROJECT_ID + '/failures/all').then(function (d) { allFmFlat.value = d; }).catch(function () { allFmFlat.value = []; }); }
'''
if old_load_all_fm in content:
    content = content.replace(old_load_all_fm, '')
    print("OK: loadAllFmFlat removed")

# Remove openRefAssoc and saveRefAssoc
old_assoc_funcs = '''        function openRefAssoc(ref) {
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
'''
if old_assoc_funcs in content:
    content = content.replace(old_assoc_funcs, '')
    print("OK: assoc functions removed")

# Replace openRefUpload + openRefUrl with openRefAdd
old_open_refs = '''        function openRefUpload() { Object.assign(refForm, { title: '', type: '其他', url: '', notes: '' }); refSelNodeIds.value = []; refSelFmIds.value = []; refFmSearch.value = ''; refNodeSearch.value = ''; selectedFile.value = null; loadAllFmFlat(); showRefUpload.value = true; }
        function openRefUrl() { Object.assign(refForm, { title: '', type: '其他', url: '', notes: '' }); refSelNodeIds.value = []; refSelFmIds.value = []; refFmSearch.value = ''; refNodeSearch.value = ''; selectedFile.value = null; loadAllFmFlat(); showRefUrl.value = true; }'''

new_open_refs = '''        function openRefAdd() { Object.assign(refForm, { title: '', type: '链接', url: '', notes: '' }); selectedFile.value = null; editingRefAdd.value = false; showRefAdd.value = true; }'''

if old_open_refs in content:
    content = content.replace(old_open_refs, new_open_refs)
    print("OK: openRefAdd replaces openRefUpload/openRefUrl")
else:
    print("FAIL: openRefUpload/openRefUrl not found")

# Replace uploadRef + saveRefUrl with saveRef
old_save_refs = '''        function uploadRef() { if (!selectedFile.value) return; var fd = new FormData(); fd.append('file', selectedFile.value); fd.append('title', refForm.title.trim()); fd.append('type', refForm.type); fd.append('node_ids', JSON.stringify(refSelNodeIds.value)); fd.append('failure_mode_ids', JSON.stringify(refSelFmIds.value)); fd.append('notes', refForm.notes); fetch('/api/v1/projects/' + PROJECT_ID + '/references/upload', { method: 'POST', body: fd }).then(function (res) { if (!res.ok) throw new Error('上传失败'); showRefUpload.value = false; loadReferences(); showToast('已上传', 'success'); }).catch(function (e) { showToast('上传失败: ' + e.message, 'warning'); }); }
        function saveRefUrl() { API.post('/api/v1/projects/' + PROJECT_ID + '/references', { title: refForm.title.trim(), type: refForm.type, node_ids: refSelNodeIds.value.slice(), failure_mode_ids: refSelFmIds.value.slice(), url: refForm.url.trim(), notes: refForm.notes }).then(function () { showRefUrl.value = false; loadReferences(); showToast('已添加', 'success'); }).catch(function (e) { showToast('保存失败: ' + e.message, 'warning'); }); }'''

new_save_refs = '''        function saveRef() {
            if (refForm.type === '链接') {
                API.post('/api/v1/projects/' + PROJECT_ID + '/references', { title: refForm.title.trim(), type: refForm.type, url: refForm.url.trim(), notes: refForm.notes }).then(function () { showRefAdd.value = false; loadReferences(); showToast('已添加', 'success'); }).catch(function (e) { showToast('保存失败: ' + e.message, 'warning'); });
            } else {
                if (!selectedFile.value) return;
                var fd = new FormData(); fd.append('file', selectedFile.value); fd.append('title', refForm.title.trim()); fd.append('type', refForm.type); fd.append('node_ids', '[]'); fd.append('failure_mode_ids', '[]'); fd.append('notes', refForm.notes);
                fetch('/api/v1/projects/' + PROJECT_ID + '/references/upload', { method: 'POST', body: fd }).then(function (res) { if (!res.ok) throw new Error('上传失败'); showRefAdd.value = false; loadReferences(); showToast('已上传', 'success'); }).catch(function (e) { showToast('上传失败: ' + e.message, 'warning'); });
            }
        }'''

if old_save_refs in content:
    content = content.replace(old_save_refs, new_save_refs)
    print("OK: saveRef replaces uploadRef/saveRefUrl")
else:
    print("FAIL: uploadRef/saveRefUrl not found")

# Remove loadAllFmFlat from tab watcher
old_watcher = "            if (val === 'references') { loadReferences(); loadAllNodesFlat(); loadAllFmFlat(); }"
new_watcher = "            if (val === 'references') { loadReferences(); loadAllNodesFlat(); }"
if old_watcher in content:
    content = content.replace(old_watcher, new_watcher)
    print("OK: tab watcher simplified")

# Update return object
old_return = '''            references: references, showRefUpload: showRefUpload, showRefUrl: showRefUrl,
            showRefAssoc: showRefAssoc, editingRefAssoc: editingRefAssoc,
            openRefAssoc: openRefAssoc, saveRefAssoc: saveRefAssoc,
            refAssocNodeIds: refAssocNodeIds, refAssocFmIds: refAssocFmIds,
            refAssocNodeSearch: refAssocNodeSearch, refAssocFmSearch: refAssocFmSearch,
            refAssocNodeFiltered: refAssocNodeFiltered, refAssocFmFiltered: refAssocFmFiltered,
            refSelFmIds: refSelFmIds, refFmSearch: refFmSearch, refFmFiltered: refFmFiltered,
            refSearchText: refSearchText, refSearchDebounce: refSearchDebounce,
            filteredRefList: filteredRefList, allFmFlat: allFmFlat,
            loadAllFmFlat: loadAllFmFlat,'''

new_return = '''            references: references, showRefAdd: showRefAdd, openRefAdd: openRefAdd, saveRef: saveRef,
            filteredRefList: filteredRefList, refSearchText: refSearchText,
            refTypeFilter: refTypeFilter, refTypeTabs: refTypeTabs,
            refTypeCount: refTypeCount, refTypeColor: refTypeColor,'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print("OK: return object simplified")
else:
    print("FAIL: return object not found")

# Replace showRefUpload with showRefAdd in template references
for old, new in [
    ('showRefUpload', 'showRefAdd'),
    ('openRefUpload', 'openRefAdd'),
    ('showRefUrl', 'showRefAdd'),
]:
    content = content.replace(old, new)
    print(f"OK: replaced {old} -> {new}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone!")
