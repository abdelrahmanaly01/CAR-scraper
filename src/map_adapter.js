// Site-specific adapter. The production Vue renderer keeps its root VNode
// on #app. The map component provides the existing Leaflet instance as mapProvide.
// No requests, source rewriting, or replacement map are involved.
() => {
  const root = document.querySelector('#app');
  const seen = new Set();
  function visit(vnode) {
    if (!vnode || typeof vnode !== 'object' || seen.has(vnode)) return null;
    seen.add(vnode);
    const component = vnode.component;
    if (component) {
      const providedMap = component.provides?.mapProvide?.value;
      const providedControl = component.provides?.layerControl?.value;
      const map = providedMap?.__v_raw || providedMap;
      const control = providedControl?.__v_raw || providedControl;
      if (map && typeof map.setView === 'function' &&
          map.getContainer() === document.querySelector('#map')) {
        return {map, control};
      }
      const match = visit(component.subTree);
      if (match) return match;
    }
    if (vnode.suspense) {
      const match = visit(vnode.suspense.activeBranch);
      if (match) return match;
    }
    if (Array.isArray(vnode.children)) {
      for (const child of vnode.children) {
        const match = visit(child);
        if (match) return match;
      }
    }
    return null;
  }
  return visit(root?._vnode);
}
