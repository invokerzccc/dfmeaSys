"""Replace DFMEA table section with new version with column visibility toggle"""
import re

path = r'C:\Users\invok\OneDrive\Codes\AI_DFMEA\YL\templates\project.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_header_extra = '''                        <div class="dfmea-cols-toggle">
                            <button class="btn btn-ghost btn-sm" @click="showColsPopover = !showColsPopover" title="选择显示列">&#9776; 列</button>
                            <div class="dfmea-cols-popover" v-if="showColsPopover" @click.stop>
                                <div class="cols-group-label">核心分析</div>
                                <label><input type="checkbox" v-model="dfmeaCol.func" @change="saveColsPref"> 功能</label>
                                <label><input type="checkbox" v-model="dfmeaCol.mode" @change="saveColsPref"> 失效模式</label>
                                <label><input type="checkbox" v-model="dfmeaCol.effect" @change="saveColsPref"> 失效影响</label>
                                <div class="cols-group-label">评分</div>
                                <label><input type="checkbox" v-model="dfmeaCol.S" @change="saveColsPref"> S — 严重度</label>
                                <label><input type="checkbox" v-model="dfmeaCol.O" @change="saveColsPref"> O — 频度</label>
                                <label><input type="checkbox" v-model="dfmeaCol.D" @change="saveColsPref"> D — 探测度</label>
                                <label><input type="checkbox" v-model="dfmeaCol.RPN" @change="saveColsPref"> RPN</label>
                                <label><input type="checkbox" v-model="dfmeaCol.AP" @change="saveColsPref"> AP</label>
                                <label><input type="checkbox" v-model="dfmeaCol.class" @change="saveColsPref"> 分类 (SC/CC)</label>
                                <div class="cols-group-label">原因 & 控制</div>
                                <label><input type="checkbox" v-model="dfmeaCol.cause" @change="saveColsPref"> 失效原因</label>
                                <label><input type="checkbox" v-model="dfmeaCol.prevent" @change="saveColsPref"> 预防控制</label>
                                <label><input type="checkbox" v-model="dfmeaCol.detect" @change="saveColsPref"> 探测控制</label>
                                <div class="cols-group-label">改进 & 管理</div>
                                <label><input type="checkbox" v-model="dfmeaCol.action" @change="saveColsPref"> 建议措施</label>
                                <label><input type="checkbox" v-model="dfmeaCol.status" @change="saveColsPref"> 状态</label>
                                <label><input type="checkbox" v-model="dfmeaCol.refs" @change="saveColsPref"> 参考资料</label>
                            </div>
                        </div>
'''

# Insert column toggle div before the "+ 添加失效行" button
old_add_btn = '<button class="btn btn-primary btn-sm" @click="openDfmeaAdd">+ 添加失效行</button>'
new_add_btn = new_header_extra + '                        ' + old_add_btn
content = content.replace(old_add_btn, new_add_btn)

# Now replace the table header and body with v-show versions

# Table header
old_thead = '''                            <thead><tr>
                                <th style="width:32px">#</th><th style="min-width:90px">功能</th><th style="min-width:100px">失效模式</th><th style="min-width:160px">失效影响</th>
                                <th style="width:48px">S</th><th style="width:48px">分类</th>
                                <th style="min-width:160px">失效原因</th><th style="width:48px">O</th>
                                <th style="min-width:160px">预防控制</th><th style="min-width:160px">探测控制</th><th style="width:48px">D</th>
                                <th style="width:60px">RPN</th><th style="width:44px">AP</th>
                                <th style="min-width:140px">建议措施</th><th style="width:55px">参考</th><th style="width:60px">状态</th>
                                <th style="width:55px">操作</th>
                            </tr></thead>'''

new_thead = '''                            <thead><tr>
                                <th style="width:32px">#</th>
                                <th style="min-width:90px" v-show="dfmeaCol.func">功能</th>
                                <th style="min-width:100px" v-show="dfmeaCol.mode">失效模式</th>
                                <th style="min-width:160px" v-show="dfmeaCol.effect">失效影响</th>
                                <th style="width:48px" v-show="dfmeaCol.S" class="col-score">S</th>
                                <th style="width:48px" v-show="dfmeaCol.class">分类</th>
                                <th style="min-width:160px" v-show="dfmeaCol.cause">失效原因</th>
                                <th style="width:48px" v-show="dfmeaCol.O" class="col-score">O</th>
                                <th style="min-width:160px" v-show="dfmeaCol.prevent">预防控制</th>
                                <th style="min-width:160px" v-show="dfmeaCol.detect">探测控制</th>
                                <th style="width:48px" v-show="dfmeaCol.D" class="col-score">D</th>
                                <th style="width:60px" v-show="dfmeaCol.RPN" class="col-score">RPN</th>
                                <th style="width:44px" v-show="dfmeaCol.AP" class="col-score">AP</th>
                                <th style="min-width:140px" v-show="dfmeaCol.action">建议措施</th>
                                <th style="width:55px" v-show="dfmeaCol.refs">参考</th>
                                <th style="width:60px" v-show="dfmeaCol.status">状态</th>
                                <th style="width:55px">操作</th>
                            </tr></thead>'''

if old_thead in content:
    content = content.replace(old_thead, new_thead)
    print("OK: thead replaced")
else:
    print("FAIL: thead not found, checking whitespace...")
    # Find the line
    for i, line in enumerate(content.split('\n')):
        if '<th style="width:32px">#' in line:
            print(f"  Found at line {i+1}: {line[:100]}")

# Table body - use regex to replace the tbody
old_tbody_start = '''                            <tbody>
                                <tr v-for="(f, idx) in failures" :key="f.id"
                                    :class="{ 'row-h': f.rpn >= 200, 'row-m': f.rpn >= 100 && f.rpn < 200 }">
                                    <td class="nowrap">[[ idx + 1 ]]</td>
                                    <td class="nowrap" :title="f.function_desc">[[ truncate(f.function_desc, 18) ]]</td>
                                    <td :title="f.mode_desc" @dblclick="editDfmea(f)">[[ truncate(f.mode_desc, 22) ]]</td>
                                    <td :title="f.potential_effect"><div v-for="(line, i) in (f.potential_effect || '').split('\\n')" :key="'e'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap" style="text-align:center"><span class="score-dot" :class="'score-' + (f.severity_S >= 7 ? 'h' : f.severity_S >= 4 ? 'm' : 'l')">[[ f.severity_S ]]</span></td>
                                    <td class="nowrap">[[ f.classification || '-' ]]</td>
                                    <td :title="f.potential_cause"><div v-for="(line, i) in (f.potential_cause || '').split('\\n')" :key="'c'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap" style="text-align:center"><span class="score-dot" :class="'score-' + (f.occurrence_O >= 7 ? 'h' : f.occurrence_O >= 4 ? 'm' : 'l')">[[ f.occurrence_O ]]</span></td>
                                    <td :title="f.prevention_control"><div v-for="(line, i) in (f.prevention_control || '').split('\\n')" :key="'p'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td :title="f.detection_control"><div v-for="(line, i) in (f.detection_control || '').split('\\n')" :key="'d'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap" style="text-align:center"><span class="score-dot" :class="'score-' + (f.detection_D >= 7 ? 'h' : f.detection_D >= 4 ? 'm' : 'l')">[[ f.detection_D ]]</span></td>
                                    <td class="nowrap"><span class="tag" :class="'tag-' + rpnLevel(f.rpn).toLowerCase()" style="font-weight:700">[[ f.rpn ]]</span></td>
                                    <td class="nowrap"><span class="tag" :class="'tag-' + f.action_priority.toLowerCase()">[[ f.action_priority ]]</span></td>
                                    <td :title="f.recommended_action"><div v-for="(line, i) in (f.recommended_action || '').split('\\n')" :key="'r'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap" style="text-align:center">
                                        <span v-if="f.linked_refs && f.linked_refs.length > 0" class="tag" style="font-size:.7rem;cursor:pointer;background:var(--accent);color:#fff" :title="f.linked_refs.map(function(r){return r.title}).join('\\n')">[[ f.linked_refs.length ]]</span>
                                        <span v-else style="color:var(--text-secondary);font-size:.75rem">-</span>
                                    </td>
                                    <td class="nowrap">[[ f.action_status || '-' ]]</td>
                                    <td class="nowrap">
                                        <button class="btn btn-ghost btn-sm" @click="editDfmea(f)" title="编辑">&#9998;</button>
                                        <button class="btn btn-ghost btn-sm" @click="deleteDfmea(f)" title="删除" style="color:var(--danger)">&#10005;</button>
                                    </td>
                                </tr>
                            </tbody>'''

new_tbody = '''                            <tbody>
                                <tr v-for="(f, idx) in failures" :key="f.id"
                                    :class="{ 'row-h': f.rpn >= 200, 'row-m': f.rpn >= 100 && f.rpn < 200 }">
                                    <td class="nowrap">[[ idx + 1 ]]</td>
                                    <td class="nowrap" :title="f.function_desc" v-show="dfmeaCol.func">[[ truncate(f.function_desc, 18) ]]</td>
                                    <td :title="f.mode_desc" @dblclick="editDfmea(f)" v-show="dfmeaCol.mode">[[ truncate(f.mode_desc, 22) ]]</td>
                                    <td :title="f.potential_effect" v-show="dfmeaCol.effect"><div v-for="(line, i) in (f.potential_effect || '').split('\\n')" :key="'e'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap col-score" style="text-align:center" v-show="dfmeaCol.S"><span class="score-dot" :class="'score-' + (f.severity_S >= 7 ? 'h' : f.severity_S >= 4 ? 'm' : 'l')">[[ f.severity_S ]]</span></td>
                                    <td class="nowrap" v-show="dfmeaCol.class">[[ f.classification || '-' ]]</td>
                                    <td :title="f.potential_cause" v-show="dfmeaCol.cause"><div v-for="(line, i) in (f.potential_cause || '').split('\\n')" :key="'c'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap col-score" style="text-align:center" v-show="dfmeaCol.O"><span class="score-dot" :class="'score-' + (f.occurrence_O >= 7 ? 'h' : f.occurrence_O >= 4 ? 'm' : 'l')">[[ f.occurrence_O ]]</span></td>
                                    <td :title="f.prevention_control" v-show="dfmeaCol.prevent"><div v-for="(line, i) in (f.prevention_control || '').split('\\n')" :key="'p'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td :title="f.detection_control" v-show="dfmeaCol.detect"><div v-for="(line, i) in (f.detection_control || '').split('\\n')" :key="'d'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap col-score" style="text-align:center" v-show="dfmeaCol.D"><span class="score-dot" :class="'score-' + (f.detection_D >= 7 ? 'h' : f.detection_D >= 4 ? 'm' : 'l')">[[ f.detection_D ]]</span></td>
                                    <td class="nowrap col-score" v-show="dfmeaCol.RPN"><span class="tag" :class="'tag-' + rpnLevel(f.rpn).toLowerCase()" style="font-weight:700">[[ f.rpn ]]</span></td>
                                    <td class="nowrap col-score" v-show="dfmeaCol.AP"><span class="tag" :class="'tag-' + f.action_priority.toLowerCase()">[[ f.action_priority ]]</span></td>
                                    <td :title="f.recommended_action" v-show="dfmeaCol.action"><div v-for="(line, i) in (f.recommended_action || '').split('\\n')" :key="'r'+i" v-show="line.trim()" style="margin-bottom:2px">[[ line ]]</div></td>
                                    <td class="nowrap" style="text-align:center" v-show="dfmeaCol.refs">
                                        <span v-if="f.linked_refs && f.linked_refs.length > 0" class="tag" style="font-size:.7rem;cursor:pointer;background:var(--accent);color:#fff" :title="f.linked_refs.map(function(r){return r.title}).join('\\n')">[[ f.linked_refs.length ]]</span>
                                        <span v-else style="color:var(--text-secondary);font-size:.75rem">-</span>
                                    </td>
                                    <td class="nowrap" v-show="dfmeaCol.status">[[ f.action_status || '-' ]]</td>
                                    <td class="nowrap">
                                        <button class="btn btn-ghost btn-sm" @click="editDfmea(f)" title="编辑">&#9998;</button>
                                        <button class="btn btn-ghost btn-sm" @click="deleteDfmea(f)" title="删除" style="color:var(--danger)">&#10005;</button>
                                    </td>
                                </tr>
                            </tbody>'''

if old_tbody_start in content:
    content = content.replace(old_tbody_start, new_tbody)
    print("OK: tbody replaced")
else:
    print("FAIL: tbody not found")
    # Try to find what's different
    idx = content.find('<td class="nowrap">[[ idx + 1 ]]</td>')
    if idx >= 0:
        print(f"  Found idx col at position {idx}")
        print(f"  Context: {content[idx-50:idx+100]}")
    # Try line by line
    for i, line in enumerate(content.split('\n')):
        if 'class="nowrap">[[ idx + 1 ]]</td>' in line:
            print(f"  Row at line {i+1}: indent={len(line)-len(line.lstrip())}")

# Now add JS state management
# Add the dfmeaCol reactive and showColsPopover ref
old_js_vars = "        var failures = ref([]);\n        var dfmeaWrapper = ref(null);"
new_js_vars = '''        var failures = ref([]);
        var showColsPopover = ref(false);
        var dfmeaCol = reactive(loadColsPref());
        function loadColsPref() {
            try { var saved = JSON.parse(localStorage.getItem('dfmea-cols') || 'null'); if (saved) return saved; } catch(e) {}
            return { func: true, mode: true, effect: true, S: true, O: true, D: true, RPN: true, AP: true, class: true, cause: true, prevent: true, detect: true, action: true, refs: false, status: true };
        }
        function saveColsPref() { localStorage.setItem('dfmea-cols', JSON.stringify(dfmeaCol)); }
        var dfmeaWrapper = ref(null);'''

if old_js_vars in content:
    content = content.replace(old_js_vars, new_js_vars)
    print("OK: JS vars replaced")
else:
    print("FAIL: JS vars not found")

# Add to return object - add after the failures/dfmeaWrapper/etc return entries
old_return = "            failures: failures, dfmeaWrapper: dfmeaWrapper, dfmeaTable: dfmeaTable,"
new_return = "            failures: failures, showColsPopover: showColsPopover, dfmeaCol: dfmeaCol, saveColsPref: saveColsPref, dfmeaWrapper: dfmeaWrapper, dfmeaTable: dfmeaTable,"

if old_return in content:
    content = content.replace(old_return, new_return)
    print("OK: return object updated")
else:
    print("FAIL: return entry not found")

# Add click-outside handler for column popover — close when clicking outside
# We'll add an event listener in the onMounted via a click handler on app-layout
# Actually, we can use a simpler approach: add a click handler on the main-content
# to close the popover when clicking elsewhere

# Instead of adding a separate handler, let's update the main-content click
# to also close the cols popover
old_main_click = '<main class="main-content" @click="hideCtxMenu">'
new_main_click = '<main class="main-content" @click="hideCtxMenu; showColsPopover = false">'

if old_main_click in content:
    content = content.replace(old_main_click, new_main_click)
    print("OK: main-content click updated")
else:
    print("FAIL: main-content click not found")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
