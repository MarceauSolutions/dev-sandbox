/**
 * Fitness Influencer AI Assistant - Chat Interface
 * Powered by dual-AI arbitration: Claude and Grok vote on task handling
 */

const API_URL = 'https://web-production-44ade.up.railway.app';

// Track conversation state
let conversationHistory = [];

/**
 * Process user request with AI arbitration
 * Both Claude and Grok vote on who should handle the request
 */
async function processUserRequest(message, files) {
    const typingIndicator = document.getElementById('typingIndicator');

    try {
        // If files are attached, use specialized handlers
        if (files && files.length > 0) {
            const response = await handleFileUpload(message, files);
            typingIndicator.classList.remove('active');
            addMessage(response, 'assistant');
            window.attachedFiles = [];
            displayAttachedFiles();
            return;
        }

        // Use AI arbitration for text requests
        const response = await handleAIChat(message);

        // Hide typing indicator
        typingIndicator.classList.remove('active');

        // Add response to chat
        addMessage(response, 'assistant');

    } catch (error) {
        typingIndicator.classList.remove('active');
        addMessage(`Sorry, I encountered an error: ${error.message}. Please try again.`, 'assistant');
    }
}

/**
 * Handle AI chat with dual-AI arbitration
 * Both Claude and Grok vote, then the winner executes
 */
async function handleAIChat(message) {
    try {
        console.log('[AI Chat] Sending request to:', `${API_URL}/api/ai/chat`);
        console.log('[AI Chat] Message:', message);

        const response = await fetch(`${API_URL}/api/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        console.log('[AI Chat] Response status:', response.status);

        const data = await response.json();
        console.log('[AI Chat] Response data:', JSON.stringify(data).substring(0, 500));

        if (!data.success) {
            throw new Error(data.error || 'Request failed');
        }

        // Format response based on task type
        console.log('[AI Chat] Formatting response for task_type:', data.task_type);
        return formatAIResponse(data);

    } catch (error) {
        // Fallback to keyword-based routing if AI arbitration fails
        console.error('[AI Chat] Error - falling back:', error);
        return await fallbackRouting(message);
    }
}

/**
 * Format AI arbitration response for display
 */
function formatAIResponse(data) {
    console.log('[formatAIResponse] Received data:', JSON.stringify(data).substring(0, 500));

    const { content, task_type, executed_by, costs, arbitration } = data;

    // Provide defaults to prevent undefined errors
    const safeCosts = costs || { total: 0, planning: 0, images: 0, video: 0 };
    const safeArbitration = arbitration || { decision: 'auto', claude_vote: { recommended: 'N/A' }, grok_vote: { recommended: 'N/A' } };

    console.log('[formatAIResponse] task_type:', task_type, 'content type:', content?.type);

    // Brand research response
    if (task_type === 'brand_research' && content && content.type === 'brand_profile') {
        const profile = content.profile;
        const handle = content.handle;

        // Format brand profile nicely
        const voiceSection = profile.brand_voice ? `
            <div style="margin: 10px 0;">
                <strong>🎤 Brand Voice:</strong><br>
                <span style="color: #FFD700;">Tone:</span> ${profile.brand_voice.tone || 'N/A'}<br>
                <span style="color: #FFD700;">Personality:</span> ${profile.brand_voice.personality || 'N/A'}
            </div>
        ` : '';

        const visualSection = profile.visual_style ? `
            <div style="margin: 10px 0;">
                <strong>🎨 Visual Style:</strong><br>
                <span style="color: #FFD700;">Aesthetic:</span> ${profile.visual_style.aesthetic || 'N/A'}<br>
                <span style="color: #FFD700;">Colors:</span> ${(profile.visual_style.color_palette || []).join(', ')}<br>
                <span style="color: #FFD700;">Photography:</span> ${profile.visual_style.photography_style || 'N/A'}
            </div>
        ` : '';

        const audienceSection = profile.target_audience ? `
            <div style="margin: 10px 0;">
                <strong>👥 Target Audience:</strong><br>
                <span style="color: #FFD700;">Demographics:</span> ${profile.target_audience.demographics || 'N/A'}<br>
                <span style="color: #FFD700;">Fitness Level:</span> ${profile.target_audience.fitness_level || 'N/A'}
            </div>
        ` : '';

        const adRecsSection = profile.ad_recommendations ? `
            <div style="margin: 10px 0;">
                <strong>📢 Ad Recommendations:</strong><br>
                <span style="color: #FFD700;">Best Formats:</span> ${(profile.ad_recommendations.best_formats || []).join(', ')}<br>
                <span style="color: #FFD700;">Messaging:</span> ${profile.ad_recommendations.messaging_angle || 'N/A'}
            </div>
        ` : '';

        return `
            <div style="background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%); border: 2px solid #FFD700; border-radius: 12px; padding: 20px; margin: 10px 0;">
                <strong style="color: #FFD700; font-size: 1.3em;">📊 Brand Profile: @${handle}</strong><br>
                <span style="font-size: 1.1em;">${profile.brand_name || handle}</span><br>
                <em style="color: #999;">${profile.tagline || ''}</em>
            </div>

            ${voiceSection}
            ${visualSection}
            ${audienceSection}

            <div style="margin: 10px 0;">
                <strong>💡 Unique Differentiator:</strong><br>
                ${profile.unique_differentiator || 'N/A'}
            </div>

            <div style="margin: 10px 0;">
                <strong>🎯 Brand Values:</strong><br>
                ${(profile.brand_values || []).join(' • ')}
            </div>

            ${adRecsSection}

            <div style="background: rgba(255,215,0,0.1); border: 1px solid #FFD700; border-radius: 8px; padding: 15px; margin-top: 15px;">
                <strong>✅ Profile Saved!</strong><br>
                <span style="font-size: 0.9em;">Now when you create ads, say "create a video ad for @${handle}" and I'll personalize it to match this brand's style!</span>
            </div>

            <details style="margin-top: 10px; font-size: 0.85em; opacity: 0.8;">
                <summary>🤖 Research Details</summary>
                <p><strong>Confidence:</strong> ${((profile.confidence_score || 0) * 100).toFixed(0)}%</p>
                <p><strong>Cost:</strong> $${safeCosts.total.toFixed(4)}</p>
            </details>
        `;
    }

    // Ad creation package response (both AIs collaborated) - handles both ad_package and ad_package_with_video
    if (task_type === 'ad_creation' && content && (content.type === 'ad_package' || content.type === 'ad_package_with_video')) {
        let imagesHtml = '';
        if (content.images && content.images.length > 0) {
            imagesHtml = '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0;">';
            content.images.forEach((img, i) => {
                imagesHtml += `
                    <div style="flex: 1; min-width: 200px; max-width: 300px;">
                        <img src="${img.url}" alt="Ad image ${i+1}" style="width: 100%; border-radius: 8px;">
                        <a href="${img.url}" class="btn btn-gold" target="_blank" download style="display: block; margin-top: 5px; font-size: 0.8em;">⬇️ Download</a>
                    </div>
                `;
            });
            imagesHtml += '</div>';
        }

        // Video section if video was generated
        let videoHtml = '';
        if (content.video && content.video.url) {
            videoHtml = `
                <div style="background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%); border: 2px solid #FFD700; border-radius: 12px; padding: 20px; margin: 20px 0;">
                    <strong style="color: #FFD700; font-size: 1.2em;">🎬 Video Ad Ready!</strong><br><br>
                    <video controls style="width: 100%; max-width: 400px; border-radius: 8px; margin: 10px 0;">
                        <source src="${content.video.url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video><br><br>
                    <a href="${content.video.url}" class="btn btn-gold" target="_blank" download style="font-weight: bold; padding: 12px 24px;">
                        ⬇️ Download Video (MP4)
                    </a>
                    <p style="margin-top: 10px; font-size: 0.85em; color: #999;">
                        15-second vertical video with music, transitions, and text overlays
                    </p>
                </div>
            `;
        }

        return `
            🎬 <strong>Advertisement Package Created!</strong><br>
            <em>Claude + Grok + Shotstack collaborated on this</em><br><br>

            ${videoHtml}

            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin: 10px 0;">
                <strong>📝 Ad Plan:</strong><br>
                ${content.plan.replace(/\n/g, '<br>')}
            </div>

            <strong>🖼️ Generated Images (${content.image_count}):</strong>
            ${imagesHtml}

            <details style="margin-top: 10px; font-size: 0.85em; opacity: 0.8;">
                <summary>🤖 Collaboration Details</summary>
                <p><strong>Workflow:</strong> ${safeArbitration.decision}</p>
                <p><strong>Planning cost:</strong> $${safeCosts.planning ? safeCosts.planning.toFixed(4) : '0.001'}</p>
                <p><strong>Image generation:</strong> $${safeCosts.images ? safeCosts.images.toFixed(2) : '0.21'}</p>
                ${safeCosts.video ? `<p><strong>Video rendering:</strong> $${safeCosts.video.toFixed(2)}</p>` : ''}
                <p><strong>Total cost:</strong> $${safeCosts.total.toFixed(2)}</p>
            </details>
        `;
    }

    // Image generation response
    if ((task_type === 'image' || task_type === 'unknown') && content && content.primary_url) {
        return `
            ✅ Image generated by <strong>${(executed_by || 'AI').toUpperCase()}</strong><br><br>
            <img src="${content.primary_url}" alt="Generated image" style="max-width: 100%; border-radius: 8px; margin: 10px 0;"><br><br>
            <a href="${content.primary_url}" class="btn btn-gold" target="_blank" download>⬇️ Download Image</a><br><br>
            <details style="margin-top: 10px; font-size: 0.85em; opacity: 0.8;">
                <summary>🤖 AI Arbitration Details</summary>
                <p><strong>Claude voted:</strong> ${safeArbitration.claude_vote.recommended}<br>
                <em>${safeArbitration.claude_vote.reasoning || ''}</em></p>
                <p><strong>Grok voted:</strong> ${safeArbitration.grok_vote.recommended}<br>
                <em>${safeArbitration.grok_vote.reasoning || ''}</em></p>
                <p><strong>Decision:</strong> ${safeArbitration.decision}</p>
                <p><strong>Cost:</strong> $${safeCosts.total.toFixed(4)}</p>
            </details>
        `;
    }

    // Text response
    if (typeof content === 'string') {
        return `
            ${content.replace(/\n/g, '<br>')}<br><br>
            <details style="margin-top: 10px; font-size: 0.85em; opacity: 0.8;">
                <summary>🤖 Handled by ${(executed_by || 'AI').toUpperCase()}</summary>
                <p><strong>Claude voted:</strong> ${safeArbitration.claude_vote.recommended}</p>
                <p><strong>Grok voted:</strong> ${safeArbitration.grok_vote.recommended}</p>
                <p><strong>Cost:</strong> $${safeCosts.total.toFixed(4)}</p>
            </details>
        `;
    }

    // Fallback
    return `Response from ${executed_by || 'AI'}: ${JSON.stringify(content)}`;
}

/**
 * Handle file uploads with specialized endpoints
 */
async function handleFileUpload(message, files) {
    const hasVideo = files.some(f => f.type.startsWith('video/'));

    if (hasVideo) {
        return await handleVideoEdit(message, files);
    }

    return await handleAdCreation(message, files);
}

/**
 * Fallback keyword-based routing when AI arbitration unavailable
 */
async function fallbackRouting(message) {
    const intent = analyzeIntent(message, []);

    switch (intent.type) {
        case 'generate_image':
            return await handleImageGeneration(message, intent);
        case 'create_ad':
            // For ad creation, try calling the API directly
            try {
                const response = await fetch(`${API_URL}/api/ai/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                const data = await response.json();
                if (data.success) {
                    return formatAIResponse(data);
                }
            } catch (e) {
                console.error('Fallback ad creation failed:', e);
            }
            return handleGeneralQuery(message);
        default:
            return handleGeneralQuery(message);
    }
}

/**
 * Analyze user intent from message and files
 */
function analyzeIntent(message, files) {
    const lowerMessage = message.toLowerCase();

    // Check for video editing
    if ((lowerMessage.includes('edit') || lowerMessage.includes('jump cut') || lowerMessage.includes('remove silence')) && files.some(f => f.type.startsWith('video/'))) {
        return { type: 'video_edit', confidence: 'high' };
    }

    // Check for ad creation
    if (lowerMessage.includes('ad') || lowerMessage.includes('advertisement') || lowerMessage.includes('promotional video')) {
        return { type: 'create_ad', confidence: 'high' };
    }

    // Check for graphic creation
    if (lowerMessage.includes('graphic') || lowerMessage.includes('instagram post') || lowerMessage.includes('create image') || lowerMessage.match(/tips|guide|infographic/)) {
        return { type: 'create_graphic', confidence: 'high' };
    }

    // Check for AI image generation
    if (lowerMessage.includes('generate') && (lowerMessage.includes('image') || lowerMessage.includes('picture') || lowerMessage.includes('ai') || lowerMessage.includes('diagram') || lowerMessage.includes('chart') || lowerMessage.includes('visual'))) {
        return { type: 'generate_image', confidence: 'high' };
    }

    // Check for email digest
    if (lowerMessage.includes('email') && (lowerMessage.includes('digest') || lowerMessage.includes('summary') || lowerMessage.includes('inbox'))) {
        return { type: 'email_digest', confidence: 'high' };
    }

    // Check for revenue analytics
    if (lowerMessage.match(/revenue|analytics|profit|expense|income/)) {
        return { type: 'revenue_analytics', confidence: 'high' };
    }

    // Check for calendar reminders
    if (lowerMessage.match(/calendar|reminder|schedule|recurring/)) {
        return { type: 'calendar_reminder', confidence: 'high' };
    }

    return { type: 'general', confidence: 'low' };
}

/**
 * Handle video editing request
 */
async function handleVideoEdit(message, files, intent) {
    const videoFile = files.find(f => f.type.startsWith('video/'));

    if (!videoFile) {
        return "I'd be happy to edit your video! Please attach a video file (MP4, MOV, or AVI) and I'll remove the silence with jump cuts.";
    }

    // Extract silence threshold from message if specified
    const thresholdMatch = message.match(/-?\d+\s*db/i);
    const silenceThreshold = thresholdMatch ? parseInt(thresholdMatch[0]) : -40;

    // Create FormData
    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('silence_threshold', silenceThreshold);
    formData.append('min_silence_duration', '0.5');

    addMessage(`Processing "${videoFile.name}"... This may take a few minutes depending on video length.`, 'assistant');

    try {
        const response = await fetch(`${API_URL}/api/video/edit`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            return `
                ✅ Video processed successfully!<br><br>
                <strong>📊 Processing Stats:</strong><br>
                • Original Size: ${data.stats.original_size_mb}MB<br>
                • Processed Size: ${data.stats.processed_size_mb}MB<br>
                • Size Reduction: ${data.stats.size_reduction_percent}%<br>
                • Jump Cuts Made: ${data.stats.cuts_made}<br>
                • Processing Time: ${data.stats.processing_time_seconds}s<br>
                • Silence Threshold: ${data.stats.silence_threshold_db}dB<br><br>
                <a href="${data.output_url}" class="btn btn-gold" download="edited_${videoFile.name}">⬇️ Download Edited Video</a>
            `;
        } else {
            throw new Error(data.message || 'Processing failed');
        }
    } catch (error) {
        throw new Error(`Video processing failed: ${error.message}`);
    }
}

/**
 * Handle graphic creation request - FULLY FUNCTIONAL
 */
async function handleGraphicCreation(message, files, intent) {
    // Extract title and points from message
    const titleMatch = message.match(/["']([^"']+)["']/);
    const title = titleMatch ? titleMatch[1] : "Fitness Tips";

    // Look for numbered lists or bullet points
    const pointsMatch = message.match(/\d+\.\s+([^\n]+)/g) ||
                        message.match(/[-•]\s+([^\n]+)/g);

    let cleanPoints;
    if (pointsMatch) {
        cleanPoints = pointsMatch.map(p => p.replace(/^\d+\.\s+|^[-•]\s+/, '').trim()).slice(0, 5);
    } else {
        // Default points
        cleanPoints = ['Eat protein', 'Lift weights', 'Stay consistent', 'Get enough sleep', 'Track progress'];
    }

    // Detect platform
    let platform = 'instagram_post';
    if (message.toLowerCase().includes('youtube')) platform = 'youtube_thumbnail';
    else if (message.toLowerCase().includes('tiktok')) platform = 'tiktok';
    else if (message.toLowerCase().includes('story')) platform = 'instagram_story';

    addMessage(`Creating branded ${platform} graphic: "${title}"...`, 'assistant');

    try {
        const response = await fetch(`${API_URL}/api/graphics/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                points: cleanPoints,
                platform: platform
            })
        });

        const data = await response.json();

        if (data.success) {
            // Handle base64 image data from updated API
            const imageUrl = data.image_data || data.output_url;
            return `
                ✅ Branded graphic created!<br><br>
                <img src="${imageUrl}" alt="Generated graphic" style="max-width: 100%; border-radius: 8px; margin: 10px 0;"><br><br>
                <strong>Title:</strong> "${title}"<br>
                <strong>Points:</strong><br>
                ${cleanPoints.map(p => `• ${p}`).join('<br>')}<br><br>
                <strong>Platform:</strong> ${platform}<br><br>
                <a href="${imageUrl}" class="btn btn-gold" download="fitness_graphic.jpg">⬇️ Download Graphic</a><br><br>
                <em>Ready to post to ${platform}!</em>
            `;
        } else {
            throw new Error(data.message || data.detail || 'Graphic creation failed');
        }
    } catch (error) {
        throw new Error(`Graphic creation failed: ${error.message}`);
    }
}

/**
 * Handle AI image generation request - FULLY FUNCTIONAL
 */
async function handleImageGeneration(message, intent) {
    // Extract prompt from message
    let prompt = message.replace(/generate|create|make|ai|image|picture/gi, '').trim();

    if (!prompt || prompt.length < 10) {
        prompt = "Fitness influencer working out in a modern gym with professional lighting";
    }

    addMessage(`Generating AI image: "${prompt}"...`, 'assistant');

    try {
        const response = await fetch(`${API_URL}/api/images/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                count: 1
            })
        });

        const data = await response.json();

        if (data.status === 'success' && data.output_url) {
            return `
                ✅ AI image generated!<br><br>
                <img src="${data.output_url}" alt="Generated image" style="max-width: 100%; border-radius: 8px; margin: 10px 0;"><br><br>
                <strong>Prompt:</strong> "${prompt}"<br>
                <strong>Cost:</strong> $${data.cost.toFixed(2)}<br><br>
                <a href="${data.output_url}" class="btn btn-gold" target="_blank" download>⬇️ Download Image</a><br><br>
                <em>Generated with Grok/xAI</em>
            `;
        } else {
            throw new Error(data.message || data.detail || 'Image generation failed');
        }
    } catch (error) {
        console.error('Image generation error:', error);
        return `
            ⚠️ Image generation failed.<br><br>
            <strong>Error:</strong> ${error.message}<br>
            <strong>Prompt:</strong> "${prompt}"<br><br>
            <em>Please try again or contact support if the issue persists.</em>
        `;
    }
}

/**
 * Handle email digest request
 */
async function handleEmailDigest(message, intent) {
    // Extract timeframe from message
    const daysMatch = message.match(/(\d+)\s*(day|week|hour)/i);
    let hours = 24;

    if (daysMatch) {
        const num = parseInt(daysMatch[1]);
        const unit = daysMatch[2].toLowerCase();

        if (unit.startsWith('week')) {
            hours = num * 24 * 7;
        } else if (unit.startsWith('day')) {
            hours = num * 24;
        } else {
            hours = num;
        }
    }

    return `
        📧 Generating email digest for the past ${hours} hours...<br><br>
        <em>Note: Email digest endpoint requires Google OAuth setup. This will categorize your emails by priority and provide suggested actions.</em><br><br>
        <strong>Categories:</strong><br>
        • Urgent Client Emails<br>
        • Business Development<br>
        • Partnership Opportunities<br>
        • General Correspondence
    `;
}

/**
 * Handle revenue analytics request
 */
async function handleRevenueAnalytics(message, intent) {
    return `
        📊 Generating revenue analytics report...<br><br>
        <em>Note: Revenue analytics requires connection to your Google Sheets. This will analyze:</em><br><br>
        • Revenue by source (coaching, products, sponsorships)<br>
        • Expenses by category<br>
        • Profit margins<br>
        • Month-over-month growth<br>
        • Top performing revenue streams<br><br>
        Please provide your Google Sheets ID to get started.
    `;
}

/**
 * Handle calendar reminder request
 */
async function handleCalendarReminder(message, intent) {
    // Extract days from message
    const dayPatterns = {
        'monday': 'MO', 'mon': 'MO',
        'tuesday': 'TU', 'tue': 'TU',
        'wednesday': 'WE', 'wed': 'WE',
        'thursday': 'TH', 'thu': 'TH',
        'friday': 'FR', 'fri': 'FR',
        'saturday': 'SA', 'sat': 'SA',
        'sunday': 'SU', 'sun': 'SU'
    };

    const lowerMsg = message.toLowerCase();
    const days = [];

    for (const [day, code] of Object.entries(dayPatterns)) {
        if (lowerMsg.includes(day)) {
            days.push(code);
        }
    }

    const daysList = days.length > 0 ? days.join(', ') : 'MO, WE, FR';

    return `
        📅 Creating recurring calendar reminder:<br>
        <strong>Days:</strong> ${daysList}<br>
        <strong>Task:</strong> ${message.split('for')[1] || 'Content posting'}<br><br>
        <em>Note: Calendar integration requires Google OAuth setup. This will create recurring reminders in your Google Calendar.</em>
    `;
}

/**
 * Handle advertisement creation request - FULLY FUNCTIONAL
 */
async function handleAdCreation(message, files, intent) {
    const hasVideo = files.some(f => f.type.startsWith('video/'));
    const hasImages = files.some(f => f.type.startsWith('image/'));

    if (!hasVideo && !hasImages) {
        return `
            🎬 I can help create an ad!<br><br>
            <strong>To get started, please upload:</strong><br>
            • Video footage (for video ads)<br>
            • Product images (for static ads)<br>
            • Or both!<br><br>
            Then I'll help you create a polished ad with:<br>
            ✅ Automatic video editing (jump cuts)<br>
            ✅ Branded graphics and overlays<br>
            ✅ AI-generated backgrounds (optional)<br>
            ✅ Platform optimization (Instagram, YouTube, TikTok)
        `;
    }

    // Extract ad details from message
    const titleMatch = message.match(/["']([^"']+)["']/);
    const title = titleMatch ? titleMatch[1] : "Fitness AI Assistant";

    // Detect if they want AI background
    const wantsBackground = message.toLowerCase().includes('background') ||
                           message.toLowerCase().includes('generate image');

    // Detect platform
    let platform = 'instagram_post';
    if (message.toLowerCase().includes('youtube')) platform = 'youtube_thumbnail';
    else if (message.toLowerCase().includes('tiktok')) platform = 'tiktok';
    else if (message.toLowerCase().includes('story')) platform = 'instagram_story';

    // Create FormData
    const formData = new FormData();

    // Add files
    if (hasVideo) {
        const videoFile = files.find(f => f.type.startsWith('video/'));
        formData.append('video', videoFile);
        formData.append('edit_video', 'true');
    }

    if (hasImages) {
        files.filter(f => f.type.startsWith('image/')).forEach(img => {
            formData.append('images', img);
        });
    }

    // Add text parameters
    formData.append('title', title);
    formData.append('tagline', 'Professional AI-Powered Automation');
    formData.append('call_to_action', 'Learn More');
    formData.append('platform', platform);

    if (wantsBackground) {
        formData.append('generate_background', 'true');
        formData.append('background_prompt', 'Modern fitness gym with equipment, professional lighting');
    }

    addMessage(`Creating your ${platform} ad with ${hasVideo ? 'video' : 'images'}... This may take a few minutes.`, 'assistant');

    try {
        const response = await fetch(`${API_URL}/api/ads/create`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            let responseHTML = `
                ✅ Ad creation complete!<br><br>
                <strong>📦 Your Assets:</strong><br>
            `;

            // List all downloads
            data.downloads.forEach(asset => {
                responseHTML += `
                    • <strong>${asset.name}:</strong> <a href="${asset.url}" class="btn btn-sm btn-gold" download>⬇️ Download</a><br>
                `;
            });

            responseHTML += `<br>
                <strong>📊 Processing Stats:</strong><br>
                • Total Assets: ${data.stats.total_assets}<br>
                • Processing Time: ${data.stats.processing_time_seconds}s<br>
                • Platform: ${platform}<br>
            `;

            if (data.stats.total_cost > 0) {
                responseHTML += `• AI Generation Cost: $${data.stats.total_cost.toFixed(2)}<br>`;
            }

            responseHTML += `<br>
                <strong>💡 Next Steps:</strong><br>
                • Download all assets above<br>
                • Combine in your favorite video editor if needed<br>
                • Add music and final touches<br>
                • Post to ${platform}!
            `;

            return responseHTML;
        } else {
            throw new Error(data.message || 'Ad creation failed');
        }
    } catch (error) {
        throw new Error(`Ad creation failed: ${error.message}`);
    }
}

/**
 * Handle general queries
 */
function handleGeneralQuery(message) {
    return `
        I can help you with:<br><br>
        <strong>🎬 Content Creation:</strong><br>
        • Edit videos with jump cuts<br>
        • Create branded graphics<br>
        • Generate AI images<br>
        • Make video advertisements<br><br>
        <strong>📊 Business Operations:</strong><br>
        • Email digests and summaries<br>
        • Revenue & expense analytics<br>
        • Calendar reminders<br><br>
        Try uploading a video and saying "edit this with jump cuts" or click the capability cards above to see example prompts!
    `;
}

/**
 * Check API status
 */
async function checkAPIStatus() {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('status-text');

    try {
        const response = await fetch(`${API_URL}/api/status`);
        const data = await response.json();

        if (data.ready) {
            statusIndicator.classList.add('status-online');
            statusIndicator.classList.remove('status-offline');
            statusText.textContent = 'System Ready';
            statusText.className = 'text-success';
        } else {
            statusIndicator.classList.add('status-online');
            statusText.textContent = 'System Online (Some features unavailable)';
            statusText.className = 'text-warning';
        }
    } catch (error) {
        statusIndicator.classList.remove('status-online');
        statusIndicator.classList.add('status-offline');
        statusText.textContent = 'System Offline';
        statusText.className = 'text-danger';
    }
}
