/**
 * TreeNodeView — Recursive tree component
 */
var TreeNodeView = {
  name: 'TreeNodeView',
  delimiters: ['[[', ']]'],
  props: { node: Object, activeId: Number, draggingId: Number, dropTarget: Object },
  emits: ['select', 'refresh', 'ctxmenu', 'drag-begin', 'drag-over', 'drag-leave', 'dropped', 'drag-end'],
  template:
    '<div class="tree-node">' +
      '<div class="tree-row"' +
        ' :class="{ active: node.id === activeId,' +
          ' \'drag-over\': dropTarget && dropTarget.nodeId === node.id,' +
          ' \'drag-over-before\': dropTarget && dropTarget.nodeId === node.id && dropTarget.pos === \'before\',' +
          ' \'drag-over-after\': dropTarget && dropTarget.nodeId === node.id && dropTarget.pos === \'after\',' +
          ' \'drag-over-inside\': dropTarget && dropTarget.nodeId === node.id && dropTarget.pos === \'inside\',' +
          ' \'is-dragging\': draggingId === node.id }"' +
        ' :draggable="true"' +
        ' @click="$emit(\'select\', node)"' +
        ' @contextmenu.stop.prevent="$emit(\'ctxmenu\', { event: $event, node: node, siblings: siblings })"' +
        ' @dragstart.stop="$emit(\'drag-begin\', { event: $event, node: node })"' +
        ' @dragover.stop.prevent="onDragOver($event)"' +
        ' @dragleave.stop="onDragLeave($event)"' +
        ' @drop.stop.prevent="$emit(\'dropped\', { event: $event, targetNode: node, pos: dropPos })"' +
        ' @dragend.stop="$emit(\'drag-end\')"' +
        ' @dblclick.stop="startRename">' +
        '<span class="tree-toggle" @click.stop="expanded = !expanded" v-if="node.children && node.children.length">[[ expanded ? \'\\u25BC\' : \'\\u25B6\' ]]</span>' +
        '<span v-else style="width:16px"></span>' +
        '<span class="tree-icon">[[ icon ]]</span>' +
        '<span class="tree-name" v-if="!renaming">[[ node.name ]]</span>' +
        '<input v-else ref="renameInput" class="tree-rename-input"' +
          ' v-model="renameValue"' +
          ' @keyup.enter="finishRename"' +
          ' @keyup.escape="renaming = false; renameValue = node.name"' +
          ' @blur="finishRename"' +
          ' @click.stop />' +
        '<span class="tree-type">[[ node.type ]]</span>' +
      '</div>' +
      '<div v-if="expanded && node.children && node.children.length" class="tree-children">' +
        '<tree-node-view v-for="c in node.children" :key="c.id"' +
          ' :node="c" :active-id="activeId"' +
          ' :dragging-id="draggingId" :drop-target="dropTarget"' +
          ' @select="function(id) { $emit(\'select\', id); }"' +
          ' @refresh="$emit(\'refresh\')"' +
          ' @ctxmenu="function(d) { $emit(\'ctxmenu\', d); }"' +
          ' @drag-begin="function(d) { $emit(\'drag-begin\', d); }"' +
          ' @drag-over="function(d) { $emit(\'drag-over\', d); }"' +
          ' @drag-leave="function(d) { $emit(\'drag-leave\', d); }"' +
          ' @dropped="function(d) { $emit(\'dropped\', d); }"' +
          ' @drag-end="$emit(\'drag-end\')" />' +
      '</div>' +
    '</div>',
  data: function () {
    return { expanded: true, renaming: false, renameValue: '', dropPos: 'inside' };
  },
  computed: {
    icon: function () {
      var icons = { '系统': '⊞', '子系统': '⊟', '部件': '⚙', '零件': '▸' };
      return icons[this.node.type] || '●';
    },
    siblings: function () { return null; },
  },
  methods: {
    onDragOver: function (ev) {
      var rect = ev.currentTarget.getBoundingClientRect();
      var y = ev.clientY - rect.top, h = rect.height;
      var pos = y < h * 0.25 ? 'before' : y > h * 0.75 ? 'after' : 'inside';
      this.dropPos = pos;
      this.$emit('drag-over', { event: ev, node: this.node, pos: pos });
    },
    onDragLeave: function (ev) { this.$emit('drag-leave', { event: ev, node: this.node }); },
    startRename: function () {
      this.renaming = true; this.renameValue = this.node.name;
      var self = this;
      this.$nextTick(function () { if (self.$refs.renameInput) self.$refs.renameInput.focus(); });
    },
    finishRename: function () {
      if (!this.renaming) return;
      this.renaming = false;
      var val = this.renameValue.trim(), self = this;
      if (val && val !== this.node.name) {
        API.put('/api/v1/structure/' + this.node.id, { name: val })
          .then(function () { self.$emit('refresh'); })
          .catch(function () { showToast('Rename failed', 'warning'); });
      }
    },
  },
};
