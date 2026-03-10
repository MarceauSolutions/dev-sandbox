const AnnotationsPage = {
  title: 'Form Annotations',
  _types: [],
  _colors: [],
  _selectedType: null,
  _selectedColor: null,

  async init() {
    try {
      const [typesRes, colorsRes] = await Promise.all([
        API.get('/api/video/add-form-annotations/types'),
        API.get('/api/video/add-form-annotations/colors')
      ]);
      this._types = typesRes.types || typesRes.annotation_types || typesRes || [];
      this._colors = colorsRes.colors || colorsRes || [];
    } catch (err) {
      Toast.error('Failed to load annotation options: ' + err.message);
      this._types = [];
      this._colors = [];
    }
  },

  render(container) {
    const typeTags = this._types.map(t => {
      const id = typeof t === 'string' ? t : t.id || t.name;
      const label = typeof t === 'string' ? t : t.name || t.label || t.id;
      return `<span class="tag" data-type="${id}">${label}</span>`;
    }).join('');

    const colorTags = this._colors.map(c => {
      const id = typeof c === 'string' ? c : c.id || c.name;
      const label = typeof c === 'string' ? c : c.name || c.label || c.id;
      const hex = typeof c === 'string' ? '' : c.hex || c.value || '';
      const swatch = hex ? `<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${hex};margin-right:6px;vertical-align:middle;border:1px solid rgba(255,255,255,0.2)"></span>` : '';
      return `<span class="tag" data-color="${id}">${swatch}${label}</span>`;
    }).join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Form Annotations</h1>
        <p>Add exercise form guides and angle indicators to your videos</p>
      </div>

      <form id="annotations-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          ${App.videoUrlField('annotations-video-url')}
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Annotation Settings</h2>
          </div>

          <div class="form-group">
            <label class="form-label">Annotation Type</label>
            <div class="grid-auto" id="annotations-type-tags">
              ${typeTags || '<p style="color:var(--text-muted)">No annotation types available</p>'}
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Color</label>
            <div class="grid-auto" id="annotations-color-tags">
              ${colorTags || '<p style="color:var(--text-muted)">No colors available</p>'}
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="annotations-exercise">Exercise</label>
            <input class="form-input" type="text" id="annotations-exercise" name="exercise"
              placeholder="e.g. Barbell Squat, Deadlift, Bench Press">
            <span class="form-hint">Name of the exercise being performed in the video</span>
          </div>

          <div class="form-group">
            <label class="form-checkbox">
              <input type="checkbox" id="annotations-show-angles" name="show_angles" checked>
              <span>Show Joint Angles</span>
            </label>
            <span class="form-hint">Display angle measurements at key joints during the movement</span>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="annotations-submit-btn">Add Annotations</button>
      </form>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Type tag selection
    const typeTags = container.querySelector('#annotations-type-tags');
    if (typeTags) {
      typeTags.addEventListener('click', (e) => {
        const tag = e.target.closest('.tag');
        if (!tag) return;
        typeTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        this._selectedType = tag.dataset.type;
      });
    }

    // Color tag selection
    const colorTags = container.querySelector('#annotations-color-tags');
    if (colorTags) {
      colorTags.addEventListener('click', (e) => {
        const tag = e.target.closest('.tag');
        if (!tag) return;
        colorTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        this._selectedColor = tag.dataset.color;
      });
    }

    App.formHandler('annotations-form', 'annotations-submit-btn', async () => {
      const videoUrl = container.querySelector('#annotations-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }
      if (!this._selectedType) { Toast.error('Please select an annotation type'); return; }

      const payload = {
        video_url: videoUrl,
        annotation_type: this._selectedType,
        exercise: container.querySelector('#annotations-exercise').value.trim(),
        show_angles: container.querySelector('#annotations-show-angles').checked
      };

      if (this._selectedColor) payload.color = this._selectedColor;

      const res = await API.post('/api/video/add-form-annotations', payload);

      if (res.job_id) {
        JobPoller.startPolling(res.job_id);
        Toast.success('Annotation job started! You will be notified when it completes.');
      } else {
        Toast.success('Annotations added successfully.');
      }
    });
  },

  destroy() {
    this._types = [];
    this._colors = [];
    this._selectedType = null;
    this._selectedColor = null;
  }
};
