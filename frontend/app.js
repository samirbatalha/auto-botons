/* Auto Botons — frontend state (Alpine.js) */

const API = '';
const SIZE_KEYS = ['38', '44', '58'];

document.addEventListener('alpine:init', () => {
  Alpine.store('app', {
    images: [],
    loading: false,
    async generatePdf() {
      return await window.__autoBotonsRoot?.generatePdf();
    },
  });
});

function autoBotons() {
  return {
    sizes: SIZE_KEYS,
    selectedSize: localStorage.getItem('selectedSize') || '38',
    specs: {},
    images: [],
    loading: false,
    loadingMsg: '',
    error: '',
    dragActive: false,
    installPrompt: null,
    cropperOpen: false,
    cropper: null,
    cropperTarget: null,

    get selectedSpec() {
      return this.specs[this.selectedSize];
    },

    get pageCountText() {
      const spec = this.selectedSpec;
      if (!spec) return '';
      const pages = Math.ceil(this.images.length / spec.slots_per_page);
      const used = this.images.length % spec.slots_per_page || spec.slots_per_page;
      if (this.images.length <= spec.slots_per_page) {
        return `${this.images.length} de ${spec.slots_per_page} slots na página`;
      }
      return `${pages} páginas A4 (${used} na última)`;
    },

    async init() {
      window.__autoBotonsRoot = this;
      Alpine.store('app').images = this.images;
      this.bindInstallPrompt();
      this.bindStoreSync();
      this.bindServiceWorker();

      try {
        const res = await fetch(`${API}/api/sizes`);
        this.specs = await res.json();
      } catch (e) {
        this.error = 'Não foi possível carregar configurações do servidor.';
      }
    },

    bindStoreSync() {
      this.$watch('images', (val) => { Alpine.store('app').images = val; });
      this.$watch('loading', (val) => { Alpine.store('app').loading = val; });
    },

    bindInstallPrompt() {
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        this.installPrompt = e;
      });
    },

    bindServiceWorker() {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
      }
    },

    selectSize(size) {
      this.selectedSize = size;
      localStorage.setItem('selectedSize', size);
    },

    async handleDrop(ev) {
      this.dragActive = false;
      await this.handleFiles(ev.dataTransfer.files);
    },

    async handleFiles(fileList) {
      const files = Array.from(fileList || []).filter((f) => f.type.startsWith('image/'));
      if (files.length === 0) return;

      this.error = '';
      this.loading = true;
      this.loadingMsg = `Processando ${files.length} imagem${files.length > 1 ? 'ns' : ''}...`;

      const fd = new FormData();
      files.forEach((f) => fd.append('files', f));
      fd.append('level', 'balanced');

      try {
        const res = await fetch(`${API}/api/process`, { method: 'POST', body: fd });
        if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
        const newImages = await res.json();
        this.images = [...this.images, ...newImages];
      } catch (e) {
        this.error = `Falha ao processar: ${e.message}`;
      } finally {
        this.loading = false;
        this.loadingMsg = '';
      }
    },

    async removeImage(id) {
      this.images = this.images.filter((i) => i.id !== id);
      try { await fetch(`${API}/api/image/${id}`, { method: 'DELETE' }); } catch (_) {}
    },

    duplicate(img) {
      const clone = { ...img, id: `${img.id}__dup_${Date.now()}` };
      this.images.push(clone);
    },

    clearAll() {
      if (!confirm('Remover todas as imagens?')) return;
      const ids = this.images.map((i) => i.id);
      this.images = [];
      ids.forEach((id) => {
        if (!id.includes('__dup_')) {
          fetch(`${API}/api/image/${id}`, { method: 'DELETE' }).catch(() => {});
        }
      });
    },

    openCropper(img) {
      this.cropperTarget = img;
      this.cropperOpen = true;
      this.$nextTick(() => {
        const el = this.$refs.cropperImg;
        const sourceId = img.id.split('__dup_')[0];
        el.src = `${API}/api/original/${sourceId}?t=${Date.now()}`;
        el.onload = () => {
          if (this.cropper) this.cropper.destroy();
          this.cropper = new Cropper(el, {
            aspectRatio: 1,
            viewMode: 1,
            dragMode: 'move',
            background: false,
            autoCropArea: 1,
            cropBoxResizable: true,
            cropBoxMovable: true,
            guides: false,
            center: true,
            highlight: false,
            modal: true,
          });
        };
      });
    },

    closeCropper() {
      if (this.cropper) { this.cropper.destroy(); this.cropper = null; }
      this.cropperOpen = false;
      this.cropperTarget = null;
    },

    async applyCrop() {
      if (!this.cropper || !this.cropperTarget) return;
      const data = this.cropper.getData(true);
      const imgEl = this.$refs.cropperImg;
      const naturalW = imgEl.naturalWidth;
      const naturalH = imgEl.naturalHeight;

      const side = Math.min(data.width, data.height);
      const crop = {
        x: Math.max(0, Math.min(data.x / naturalW, 1)),
        y: Math.max(0, Math.min(data.y / naturalH, 1)),
        size: Math.max(0.01, Math.min(side / Math.min(naturalW, naturalH), 1)),
      };
      const sourceId = this.cropperTarget.id.split('__dup_')[0];

      this.loading = true;
      this.loadingMsg = 'Aplicando recorte...';

      try {
        const res = await fetch(`${API}/api/recrop`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_id: sourceId, crop }),
        });
        if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
        const updated = await res.json();
        const bust = `?t=${Date.now()}`;
        this.images = this.images.map((i) =>
          i.id.startsWith(sourceId)
            ? { ...i, preview_url: `${API}/api/preview/${sourceId}${bust}` }
            : i
        );
        this.closeCropper();
      } catch (e) {
        this.error = `Falha ao aplicar recorte: ${e.message}`;
      } finally {
        this.loading = false;
        this.loadingMsg = '';
      }
    },

    async generatePdf() {
      if (this.images.length === 0) return;
      this.error = '';
      this.loading = true;
      this.loadingMsg = 'Gerando PDF...';

      try {
        const ids = this.images.map((i) => i.id.split('__dup_')[0]);
        const res = await fetch(`${API}/api/generate-pdf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ button_size: this.selectedSize, image_ids: ids }),
        });
        if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `botons_${this.selectedSize}mm.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (e) {
        this.error = `Falha ao gerar PDF: ${e.message}`;
      } finally {
        this.loading = false;
        this.loadingMsg = '';
      }
    },
  };
}

function autoBotonsFooter() {
  return {};
}
