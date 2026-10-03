(() => {
    const picker = document.querySelector('[data-guide-attraction-picker]');
    if (!picker) {
        return;
    }

    const searchUrl = picker.dataset.searchUrl;
    const keywordInput = picker.querySelector('[data-attraction-keyword]');
    const searchButton = picker.querySelector('[data-attraction-search]');
    const resultsPanel = picker.querySelector('[data-attraction-results]');
    const selectedPanel = picker.querySelector('[data-attraction-selected-list]');
    const selectedIds = new Set();

    function syncSelectedIds() {
        // 读取服务端回填的已选景点，避免重复添加。
        selectedPanel.querySelectorAll('[data-selected-attraction]').forEach((item) => {
            selectedIds.add(String(item.dataset.id));
        });
    }

    function updateEmptyState() {
        // 根据已选景点数量显示或隐藏空状态。
        const emptyNode = selectedPanel.querySelector('[data-empty-selected]');
        const hasSelected = selectedPanel.querySelector('[data-selected-attraction]');
        if (emptyNode) {
            emptyNode.hidden = Boolean(hasSelected);
        }
    }

    function buildLabel(attraction) {
        // 拼接城市、区域和景点名称作为展示文本。
        const parts = [attraction.city_name];
        if (attraction.area) {
            parts.push(attraction.area);
        }
        parts.push(attraction.name);
        return parts.filter(Boolean).join(' · ');
    }

    function escapeHtml(value) {
        // 转义接口返回文本，避免特殊字符破坏页面结构。
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function addAttraction(attraction) {
        // 已经添加过的景点不重复创建隐藏字段。
        const attractionId = String(attraction.id);
        if (selectedIds.has(attractionId)) {
            return;
        }

        // 创建选中标签和提交用隐藏 input。
        const item = document.createElement('div');
        item.className = 'guide-selected-attraction-cartoon';
        item.dataset.selectedAttraction = '1';
        item.dataset.id = attractionId;
        item.dataset.label = buildLabel(attraction);
        const safeLabel = escapeHtml(buildLabel(attraction));
        item.innerHTML = `
            <input type="hidden" name="attraction_ids" value="${attractionId}">
            <span>${safeLabel}</span>
            <button type="button" data-remove-attraction>移除</button>
        `;
        selectedPanel.appendChild(item);
        selectedIds.add(attractionId);
        updateEmptyState();
    }

    function renderResults(attractions) {
        // 将接口返回的景点渲染成可添加的结果列表。
        if (!attractions.length) {
            resultsPanel.innerHTML = '<p>没有搜索到匹配的景点。</p>';
            return;
        }

        resultsPanel.innerHTML = attractions.map((attraction) => {
            const label = buildLabel(attraction);
            const score = Number(attraction.score || 0).toFixed(1);
            const imageHtml = attraction.image
                ? `<img src="${escapeHtml(attraction.image)}" alt="${escapeHtml(attraction.name)}">`
                : `<span>${escapeHtml(attraction.name.slice(0, 1))}</span>`;
            return `
                <article class="guide-attraction-result-cartoon">
                    <div class="guide-attraction-result-cover-cartoon">${imageHtml}</div>
                    <div>
                        <strong>${escapeHtml(attraction.name)}</strong>
                        <p>${escapeHtml(label)} · 评分 ${score}</p>
                    </div>
                    <button
                        type="button"
                        data-add-attraction
                        data-id="${attraction.id}"
                        data-name="${escapeHtml(attraction.name)}"
                        data-city-name="${escapeHtml(attraction.city_name)}"
                        data-area="${escapeHtml(attraction.area || '')}"
                        data-score="${attraction.score || 0}"
                        data-image="${escapeHtml(attraction.image || '')}"
                    >添加</button>
                </article>
            `;
        }).join('');
    }

    async function searchAttractions() {
        // 校验搜索关键词，避免提交空搜索。
        const keyword = keywordInput.value.trim();
        if (!keyword) {
            resultsPanel.innerHTML = '<p>请输入景点名、城市、区域或标签再搜索。</p>';
            keywordInput.focus();
            return;
        }

        // 调用后端搜索接口并渲染结果。
        resultsPanel.innerHTML = '<p>正在搜索景点...</p>';
        const response = await fetch(`${searchUrl}?keyword=${encodeURIComponent(keyword)}`, {
            credentials: 'same-origin',
        });
        if (!response.ok) {
            resultsPanel.innerHTML = '<p>搜索失败，请稍后再试。</p>';
            return;
        }
        const data = await response.json();
        renderResults(data.results || []);
    }

    // 绑定搜索按钮和回车搜索。
    searchButton.addEventListener('click', searchAttractions);
    keywordInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchAttractions();
        }
    });

    // 使用事件委托处理添加和移除。
    picker.addEventListener('click', (event) => {
        const addButton = event.target.closest('[data-add-attraction]');
        if (addButton) {
            addAttraction({
                id: addButton.dataset.id,
                name: addButton.dataset.name,
                city_name: addButton.dataset.cityName,
                area: addButton.dataset.area,
                score: addButton.dataset.score,
                image: addButton.dataset.image,
            });
            return;
        }

        const removeButton = event.target.closest('[data-remove-attraction]');
        if (removeButton) {
            const item = removeButton.closest('[data-selected-attraction]');
            selectedIds.delete(String(item.dataset.id));
            item.remove();
            updateEmptyState();
        }
    });

    syncSelectedIds();
    updateEmptyState();
})();
