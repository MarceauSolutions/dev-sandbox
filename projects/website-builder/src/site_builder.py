#!/usr/bin/env python3
"""
site_builder.py - Static Website Generator

Generates complete HTML/CSS/JS websites from research and content data.
Uses Tailwind CSS via CDN for styling.

Enhanced with personality-driven styling:
- Dynamic typography based on brand voice
- Border radius matching brand personality
- Animation levels based on visual identity
- Color schemes from personality synthesis

Usage:
    from site_builder import build_site, build_personality_site

    # Basic build
    site_files = build_site(research, content, output_dir="./output")

    # Personality-driven build
    site_files = build_personality_site(research, content, output_dir="./output")
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class SiteBuilder:
    """
    Static website generator.

    Combines research data and generated content into
    a complete, deployable static website.
    """

    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def build_site(
        self,
        research: Dict[str, Any],
        content: Dict[str, Any],
        output_dir: str = "./output"
    ) -> Dict[str, str]:
        """
        Build complete static website.

        Args:
            research: Research data from ResearchEngine
            content: Content from ContentGenerator
            output_dir: Directory to output files

        Returns:
            Dictionary of {filename: filepath}
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        company = research.get("company", {})
        owner = research.get("owner", {})
        colors = research.get("color_scheme", {})

        # Generate HTML
        html = self._generate_html(company, owner, content, colors)

        # Write files
        files = {}

        # Main HTML
        index_path = output_path / "index.html"
        with open(index_path, "w") as f:
            f.write(html)
        files["index.html"] = str(index_path)

        # Generate additional pages if needed
        # For now, single-page site

        return files

    def _generate_html(
        self,
        company: Dict[str, Any],
        owner: Dict[str, Any],
        content: Dict[str, Any],
        colors: Dict[str, str]
    ) -> str:
        """Generate complete HTML page."""

        hero = content.get("hero", {})
        about = content.get("about", {})
        services = content.get("services", [])
        testimonials = content.get("testimonials", [])
        contact = content.get("contact", {})
        seo = content.get("seo", {})
        footer_tagline = content.get("footer_tagline", "")

        # Color scheme
        primary = colors.get("primary", "#1a1a2e")
        secondary = colors.get("secondary", "#667eea")
        accent = colors.get("accent", "#4ade80")

        # Build services HTML
        services_html = ""
        for service in services:
            benefits_html = "".join([
                f'<li class="flex items-center gap-2"><svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>{benefit}</li>'
                for benefit in service.get("benefits", [])
            ])
            services_html += f'''
            <div class="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow">
                <div class="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center mb-6">
                    <span class="text-2xl text-white">★</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-3">{service.get("name", "Service")}</h3>
                <p class="text-gray-600 mb-4">{service.get("description", "")}</p>
                <ul class="space-y-2 text-gray-700">
                    {benefits_html}
                </ul>
            </div>
            '''

        # Build testimonials HTML
        testimonials_html = ""
        for testimonial in testimonials:
            testimonials_html += f'''
            <div class="bg-white rounded-2xl shadow-lg p-8">
                <div class="flex items-center gap-1 mb-4">
                    {"".join(['<span class="text-yellow-400">★</span>' for _ in range(5)])}
                </div>
                <p class="text-gray-700 italic mb-6">"{testimonial.get("quote", "")}"</p>
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                        {testimonial.get("author", "A")[0]}
                    </div>
                    <div>
                        <p class="font-semibold text-gray-900">{testimonial.get("author", "Customer")}</p>
                        <p class="text-gray-500 text-sm">{testimonial.get("title", "")}</p>
                    </div>
                </div>
            </div>
            '''

        # Social links
        social_html = ""
        social_media = company.get("social_media", {})
        for platform, url in social_media.items():
            if url:
                social_html += f'<a href="{url}" class="text-gray-400 hover:text-white transition-colors">{platform.title()}</a>'

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{seo.get("title", company.get("name", "Website"))}</title>
    <meta name="description" content="{seo.get("description", "")}">
    <meta name="keywords" content="{", ".join(seo.get("keywords", []))}">

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Custom Colors -->
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: '{primary}',
                        secondary: '{secondary}',
                        accent: '{accent}'
                    }}
                }}
            }}
        }}
    </script>

    <style>
        html {{ scroll-behavior: smooth; }}
        .gradient-bg {{ background: linear-gradient(135deg, {primary} 0%, {secondary} 100%); }}
    </style>
</head>
<body class="antialiased">

    <!-- Navigation -->
    <nav class="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <a href="#" class="text-xl font-bold text-gray-900">{company.get("name", "Company")}</a>
                <div class="hidden md:flex items-center gap-8">
                    <a href="#about" class="text-gray-600 hover:text-gray-900 transition-colors">About</a>
                    <a href="#services" class="text-gray-600 hover:text-gray-900 transition-colors">Services</a>
                    <a href="#testimonials" class="text-gray-600 hover:text-gray-900 transition-colors">Testimonials</a>
                    <a href="#contact" class="px-5 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-full font-medium hover:shadow-lg transition-shadow">
                        {hero.get("cta_primary", "Contact")}
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="gradient-bg min-h-screen flex items-center pt-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
            <div class="max-w-3xl">
                <h1 class="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
                    {hero.get("headline", "Welcome")}
                </h1>
                <p class="text-xl text-white/80 mb-8">
                    {hero.get("subheadline", "")}
                </p>
                <div class="flex flex-wrap gap-4">
                    <a href="#contact" class="px-8 py-4 bg-white text-gray-900 rounded-full font-semibold hover:shadow-xl transition-shadow">
                        {hero.get("cta_primary", "Get Started")}
                    </a>
                    <a href="#about" class="px-8 py-4 border-2 border-white text-white rounded-full font-semibold hover:bg-white hover:text-gray-900 transition-all">
                        {hero.get("cta_secondary", "Learn More")}
                    </a>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid md:grid-cols-2 gap-12 items-center">
                <div>
                    <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                        {about.get("title", "About Us")}
                    </h2>
                    <p class="text-gray-600 text-lg mb-6">
                        {about.get("story", "")}
                    </p>
                    <p class="text-gray-700 font-medium italic border-l-4 border-indigo-500 pl-4">
                        {about.get("mission", "")}
                    </p>
                </div>
                <div class="bg-white rounded-2xl shadow-lg p-8">
                    <div class="flex items-center gap-4 mb-4">
                        <div class="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                            {owner.get("name", "O")[0]}
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">{owner.get("name", "Founder")}</h3>
                            <p class="text-indigo-600">{owner.get("title", "Owner")}</p>
                        </div>
                    </div>
                    <p class="text-gray-600">
                        {about.get("founder_bio", "")}
                    </p>
                </div>
            </div>
        </div>
    </section>

    <!-- Services Section -->
    <section id="services" class="py-20">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Our Services</h2>
                <p class="text-gray-600 text-lg max-w-2xl mx-auto">
                    Discover how we can help you achieve your goals
                </p>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {services_html}
            </div>
        </div>
    </section>

    <!-- Testimonials Section -->
    <section id="testimonials" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">What Our Clients Say</h2>
                <p class="text-gray-600 text-lg">Real results from real people</p>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {testimonials_html}
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-20">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="max-w-2xl mx-auto text-center">
                <h2 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                    {contact.get("title", "Get In Touch")}
                </h2>
                <p class="text-gray-600 text-lg mb-8">
                    {contact.get("subtitle", "")}
                </p>

                <form class="space-y-6 text-left">
                    <div class="grid md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
                            <input type="text" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent" placeholder="Your name">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
                            <input type="email" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent" placeholder="you@example.com">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                        <input type="tel" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent" placeholder="(555) 123-4567">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Message</label>
                        <textarea rows="4" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent" placeholder="How can we help you?"></textarea>
                    </div>
                    <button type="submit" class="w-full px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-xl transition-shadow">
                        {contact.get("cta", "Send Message")}
                    </button>
                </form>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="gradient-bg py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col md:flex-row justify-between items-center gap-6">
                <div>
                    <h3 class="text-xl font-bold text-white mb-2">{company.get("name", "Company")}</h3>
                    <p class="text-white/70">{footer_tagline}</p>
                </div>
                <div class="flex items-center gap-6">
                    {social_html if social_html else '<span class="text-white/70">© ' + str(datetime.now().year) + '</span>'}
                </div>
            </div>
            {f'<p class="text-white/50 text-center mt-8 text-sm">{company.get("location", "")}</p>' if company.get("location") else ""}
        </div>
    </footer>

    <!-- Smooth scroll for anchor links -->
    <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({{
                    behavior: 'smooth'
                }});
            }});
        }});
    </script>

</body>
</html>'''

        return html

    def build_personality_site(
        self,
        research: Dict[str, Any],
        content: Dict[str, Any],
        output_dir: str = "./output"
    ) -> Dict[str, str]:
        """
        Build website with personality-driven styling.

        Uses brand_personality data to customize:
        - Typography (fonts, weights)
        - Border radius (sharp to pill)
        - Shadows (none to dramatic)
        - Animations (none to dynamic)
        - Layout spacing

        Args:
            research: Research data with brand_personality
            content: Content from ContentGenerator
            output_dir: Directory to output files

        Returns:
            Dictionary of {filename: filepath}
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        company = research.get("company", {})
        owner = research.get("owner", {})
        colors = research.get("color_scheme", {})
        personality = research.get("brand_personality", {})

        # Extract visual identity settings
        visual = personality.get("visual_identity", {}) if personality else {}

        # Generate personality-styled HTML
        html = self._generate_personality_html(
            company, owner, content, colors, visual, personality
        )

        # Write files
        files = {}
        index_path = output_path / "index.html"
        with open(index_path, "w") as f:
            f.write(html)
        files["index.html"] = str(index_path)

        return files

    def _generate_personality_html(
        self,
        company: Dict[str, Any],
        owner: Dict[str, Any],
        content: Dict[str, Any],
        colors: Dict[str, str],
        visual: Dict[str, Any],
        personality: Dict[str, Any]
    ) -> str:
        """Generate HTML with personality-driven styling."""

        hero = content.get("hero", {})
        about = content.get("about", {})
        services = content.get("services", [])
        testimonials = content.get("testimonials", [])
        contact = content.get("contact", {})
        seo = content.get("seo", {})
        footer_tagline = content.get("footer_tagline", "")

        # Colors
        primary = colors.get("primary", "#1a1a2e")
        secondary = colors.get("secondary", "#667eea")
        accent = colors.get("accent", "#4ade80")
        bg_color = colors.get("background", "#ffffff")
        text_color = colors.get("text", "#1f2937")

        # Get styling from visual identity
        styles = self._get_personality_styles(visual)

        # Build services HTML with personality styling
        services_html = self._build_services_html(services, styles)

        # Build testimonials HTML with personality styling
        testimonials_html = self._build_testimonials_html(testimonials, styles)

        # Social links
        social_html = ""
        social_media = company.get("social_media", {})
        for platform, url in social_media.items():
            if url:
                social_html += f'<a href="{url}" class="text-gray-400 hover:text-white transition-colors">{platform.title()}</a>'

        # Font imports based on heading style
        font_import = self._get_font_import(visual.get("heading_style", "bold_sans"))

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{seo.get("title", company.get("name", "Website"))}</title>
    <meta name="description" content="{seo.get("description", "")}">
    <meta name="keywords" content="{", ".join(seo.get("keywords", []))}">

    <!-- Fonts -->
    {font_import}

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Custom Configuration -->
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: '{primary}',
                        secondary: '{secondary}',
                        accent: '{accent}'
                    }},
                    fontFamily: {{
                        heading: {styles['font_heading']},
                        body: {styles['font_body']}
                    }},
                    borderRadius: {{
                        'brand': '{styles['border_radius']}'
                    }}
                }}
            }}
        }}
    </script>

    <style>
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: {styles['body_font_css']}; color: {text_color}; background: {bg_color}; }}
        h1, h2, h3, h4, h5, h6 {{ font-family: {styles['heading_font_css']}; }}
        .gradient-bg {{ background: linear-gradient(135deg, {primary} 0%, {secondary} 100%); }}
        {styles['custom_css']}
    </style>
</head>
<body class="antialiased">

    <!-- Navigation -->
    <nav class="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md {styles['shadow']}">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <a href="#" class="text-xl font-bold text-gray-900 font-heading">{company.get("name", "Company")}</a>
                <div class="hidden md:flex items-center gap-8">
                    <a href="#about" class="text-gray-600 hover:text-gray-900 {styles['transition']}">About</a>
                    <a href="#services" class="text-gray-600 hover:text-gray-900 {styles['transition']}">Services</a>
                    <a href="#testimonials" class="text-gray-600 hover:text-gray-900 {styles['transition']}">Testimonials</a>
                    <a href="#contact" class="px-5 py-2 bg-gradient-to-r from-primary to-secondary text-white {styles['btn_radius']} font-medium {styles['hover_effect']} {styles['transition']}">
                        {hero.get("cta_primary", "Contact")}
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="gradient-bg min-h-screen flex items-center pt-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
            <div class="max-w-3xl {styles['hero_animation']}">
                <h1 class="text-4xl md:text-6xl {styles['heading_weight']} text-white mb-6 leading-tight font-heading">
                    {hero.get("headline", "Welcome")}
                </h1>
                <p class="text-xl text-white/80 mb-8">
                    {hero.get("subheadline", "")}
                </p>
                <div class="flex flex-wrap gap-4">
                    <a href="#contact" class="px-8 py-4 bg-white text-gray-900 {styles['btn_radius']} font-semibold {styles['hover_effect']} {styles['transition']}">
                        {hero.get("cta_primary", "Get Started")}
                    </a>
                    <a href="#about" class="px-8 py-4 border-2 border-white text-white {styles['btn_radius']} font-semibold hover:bg-white hover:text-gray-900 {styles['transition']}">
                        {hero.get("cta_secondary", "Learn More")}
                    </a>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid md:grid-cols-2 gap-12 items-center">
                <div>
                    <h2 class="text-3xl md:text-4xl {styles['heading_weight']} text-gray-900 mb-6 font-heading">
                        {about.get("title", "About Us")}
                    </h2>
                    <p class="text-gray-600 text-lg mb-6">
                        {about.get("story", "")}
                    </p>
                    <p class="text-gray-700 font-medium italic border-l-4 border-primary pl-4">
                        {about.get("mission", "")}
                    </p>
                </div>
                <div class="bg-white {styles['card_radius']} {styles['card_shadow']} p-8">
                    <div class="flex items-center gap-4 mb-4">
                        <div class="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white text-2xl font-bold">
                            {owner.get("name", "O")[0]}
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">{owner.get("name", "Founder")}</h3>
                            <p class="text-primary">{owner.get("title", "Owner")}</p>
                        </div>
                    </div>
                    <p class="text-gray-600">
                        {about.get("founder_bio", "")}
                    </p>
                </div>
            </div>
        </div>
    </section>

    <!-- Services Section -->
    <section id="services" class="py-20">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-4xl {styles['heading_weight']} text-gray-900 mb-4 font-heading">Our Services</h2>
                <p class="text-gray-600 text-lg max-w-2xl mx-auto">
                    Discover how we can help you achieve your goals
                </p>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {services_html}
            </div>
        </div>
    </section>

    <!-- Testimonials Section -->
    <section id="testimonials" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-4xl {styles['heading_weight']} text-gray-900 mb-4 font-heading">What Our Clients Say</h2>
                <p class="text-gray-600 text-lg">Real results from real people</p>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {testimonials_html}
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-20">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="max-w-2xl mx-auto text-center">
                <h2 class="text-3xl md:text-4xl {styles['heading_weight']} text-gray-900 mb-4 font-heading">
                    {contact.get("title", "Get In Touch")}
                </h2>
                <p class="text-gray-600 text-lg mb-8">
                    {contact.get("subtitle", "")}
                </p>

                <form class="space-y-6 text-left">
                    <div class="grid md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
                            <input type="text" class="w-full px-4 py-3 border border-gray-300 {styles['input_radius']} focus:ring-2 focus:ring-primary focus:border-transparent {styles['transition']}" placeholder="Your name">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
                            <input type="email" class="w-full px-4 py-3 border border-gray-300 {styles['input_radius']} focus:ring-2 focus:ring-primary focus:border-transparent {styles['transition']}" placeholder="you@example.com">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                        <input type="tel" class="w-full px-4 py-3 border border-gray-300 {styles['input_radius']} focus:ring-2 focus:ring-primary focus:border-transparent {styles['transition']}" placeholder="(555) 123-4567">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Message</label>
                        <textarea rows="4" class="w-full px-4 py-3 border border-gray-300 {styles['input_radius']} focus:ring-2 focus:ring-primary focus:border-transparent {styles['transition']}" placeholder="How can we help you?"></textarea>
                    </div>
                    <button type="submit" class="w-full px-8 py-4 bg-gradient-to-r from-primary to-secondary text-white {styles['btn_radius']} font-semibold {styles['hover_effect']} {styles['transition']}">
                        {contact.get("cta", "Send Message")}
                    </button>
                </form>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="gradient-bg py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col md:flex-row justify-between items-center gap-6">
                <div>
                    <h3 class="text-xl font-bold text-white mb-2 font-heading">{company.get("name", "Company")}</h3>
                    <p class="text-white/70">{footer_tagline}</p>
                </div>
                <div class="flex items-center gap-6">
                    {social_html if social_html else '<span class="text-white/70">© ' + str(datetime.now().year) + '</span>'}
                </div>
            </div>
            {f'<p class="text-white/50 text-center mt-8 text-sm">{company.get("location", "")}</p>' if company.get("location") else ""}
        </div>
    </footer>

    <!-- Smooth scroll for anchor links -->
    <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({{
                    behavior: 'smooth'
                }});
            }});
        }});
    </script>

</body>
</html>'''

        return html

    def _get_personality_styles(self, visual: Dict[str, Any]) -> Dict[str, str]:
        """Get CSS classes and styles from visual identity settings."""

        # Border radius mapping
        border_radius_map = {
            "none": {"card": "rounded-none", "btn": "rounded-none", "input": "rounded-none", "value": "0"},
            "subtle": {"card": "rounded-lg", "btn": "rounded-md", "input": "rounded-md", "value": "0.5rem"},
            "rounded": {"card": "rounded-2xl", "btn": "rounded-xl", "input": "rounded-lg", "value": "1rem"},
            "pill": {"card": "rounded-3xl", "btn": "rounded-full", "input": "rounded-full", "value": "1.5rem"},
        }

        # Shadow mapping
        shadow_map = {
            "none": {"shadow": "", "card": ""},
            "subtle": {"shadow": "shadow-sm", "card": "shadow-md"},
            "medium": {"shadow": "shadow-md", "card": "shadow-lg"},
            "dramatic": {"shadow": "shadow-lg", "card": "shadow-2xl"},
        }

        # Animation mapping
        animation_map = {
            "none": {"transition": "", "hover": "", "hero": ""},
            "subtle": {"transition": "transition-all duration-200", "hover": "hover:shadow-lg", "hero": ""},
            "moderate": {"transition": "transition-all duration-300", "hover": "hover:shadow-xl hover:-translate-y-1", "hero": "animate-fade-in"},
            "dynamic": {"transition": "transition-all duration-300 ease-out", "hover": "hover:shadow-2xl hover:-translate-y-2 hover:scale-105", "hero": "animate-slide-up"},
        }

        # Heading style mapping
        heading_map = {
            "bold_sans": {"weight": "font-bold", "font": "['Inter', 'system-ui', 'sans-serif']", "css": "'Inter', system-ui, sans-serif"},
            "elegant_serif": {"weight": "font-semibold", "font": "['Playfair Display', 'Georgia', 'serif']", "css": "'Playfair Display', Georgia, serif"},
            "modern_geometric": {"weight": "font-bold", "font": "['Poppins', 'system-ui', 'sans-serif']", "css": "'Poppins', system-ui, sans-serif"},
            "playful": {"weight": "font-bold", "font": "['Nunito', 'system-ui', 'sans-serif']", "css": "'Nunito', system-ui, sans-serif"},
            "classic": {"weight": "font-semibold", "font": "['Merriweather', 'Georgia', 'serif']", "css": "'Merriweather', Georgia, serif"},
        }

        # Get settings with defaults
        border_radius = visual.get("border_radius", "rounded")
        shadow_intensity = visual.get("shadow_intensity", "subtle")
        animation_level = visual.get("animation_level", "subtle")
        heading_style = visual.get("heading_style", "bold_sans")

        radius_styles = border_radius_map.get(border_radius, border_radius_map["rounded"])
        shadow_styles = shadow_map.get(shadow_intensity, shadow_map["subtle"])
        anim_styles = animation_map.get(animation_level, animation_map["subtle"])
        heading_styles = heading_map.get(heading_style, heading_map["bold_sans"])

        # Build custom CSS for animations if needed
        custom_css = ""
        if animation_level in ["moderate", "dynamic"]:
            custom_css = """
        @keyframes fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slide-up {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fade-in 0.6s ease-out; }
        .animate-slide-up { animation: slide-up 0.8s ease-out; }
            """

        return {
            "card_radius": radius_styles["card"],
            "btn_radius": radius_styles["btn"],
            "input_radius": radius_styles["input"],
            "border_radius": radius_styles["value"],
            "shadow": shadow_styles["shadow"],
            "card_shadow": shadow_styles["card"],
            "transition": anim_styles["transition"],
            "hover_effect": anim_styles["hover"],
            "hero_animation": anim_styles["hero"],
            "heading_weight": heading_styles["weight"],
            "font_heading": heading_styles["font"],
            "heading_font_css": heading_styles["css"],
            "font_body": "['Inter', 'system-ui', 'sans-serif']",
            "body_font_css": "'Inter', system-ui, sans-serif",
            "custom_css": custom_css,
        }

    def _get_font_import(self, heading_style: str) -> str:
        """Get Google Fonts import for heading style."""
        font_imports = {
            "bold_sans": '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
            "elegant_serif": '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">',
            "modern_geometric": '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">',
            "playful": '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Inter:wght@400;500&display=swap" rel="stylesheet">',
            "classic": '<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">',
        }
        return font_imports.get(heading_style, font_imports["bold_sans"])

    def _build_services_html(self, services: List[Dict], styles: Dict[str, str]) -> str:
        """Build services section HTML with personality styling."""
        services_html = ""
        for service in services:
            benefits_html = "".join([
                f'<li class="flex items-center gap-2"><svg class="w-5 h-5 text-accent" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>{benefit}</li>'
                for benefit in service.get("benefits", [])
            ])
            services_html += f'''
            <div class="bg-white {styles['card_radius']} {styles['card_shadow']} p-8 {styles['hover_effect']} {styles['transition']}">
                <div class="w-14 h-14 bg-gradient-to-br from-primary to-secondary {styles['card_radius']} flex items-center justify-center mb-6">
                    <span class="text-2xl text-white">★</span>
                </div>
                <h3 class="text-xl {styles['heading_weight']} text-gray-900 mb-3 font-heading">{service.get("name", "Service")}</h3>
                <p class="text-gray-600 mb-4">{service.get("description", "")}</p>
                <ul class="space-y-2 text-gray-700">
                    {benefits_html}
                </ul>
            </div>
            '''
        return services_html

    def _build_testimonials_html(self, testimonials: List[Dict], styles: Dict[str, str]) -> str:
        """Build testimonials section HTML with personality styling."""
        testimonials_html = ""
        for testimonial in testimonials:
            testimonials_html += f'''
            <div class="bg-white {styles['card_radius']} {styles['card_shadow']} p-8 {styles['hover_effect']} {styles['transition']}">
                <div class="flex items-center gap-1 mb-4">
                    {"".join(['<span class="text-yellow-400">★</span>' for _ in range(5)])}
                </div>
                <p class="text-gray-700 italic mb-6">"{testimonial.get("quote", "")}"</p>
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white font-bold">
                        {testimonial.get("author", "A")[0]}
                    </div>
                    <div>
                        <p class="font-semibold text-gray-900">{testimonial.get("author", "Customer")}</p>
                        <p class="text-gray-500 text-sm">{testimonial.get("title", "")}</p>
                    </div>
                </div>
            </div>
            '''
        return testimonials_html


def build_site(
    research: Dict[str, Any],
    content: Dict[str, Any],
    output_dir: str = "./output"
) -> Dict[str, str]:
    """Build static website from research and content."""
    builder = SiteBuilder()
    return builder.build_site(research, content, output_dir)


def build_personality_site(
    research: Dict[str, Any],
    content: Dict[str, Any],
    output_dir: str = "./output"
) -> Dict[str, str]:
    """Build personality-driven website from research and content."""
    builder = SiteBuilder()
    return builder.build_personality_site(research, content, output_dir)


if __name__ == "__main__":
    # Test with sample data
    sample_research = {
        "company": {
            "name": "Project Evolve",
            "industry": "Fitness",
            "location": "Naples, FL",
            "social_media": {"instagram": "https://instagram.com/projectevolve"}
        },
        "owner": {"name": "Jake Raleigh", "title": "Owner"},
        "color_scheme": {
            "primary": "#1a1a2e",
            "secondary": "#667eea",
            "accent": "#4ade80"
        }
    }

    sample_content = {
        "hero": {
            "headline": "Transform Your Body, Transform Your Life",
            "subheadline": "Small-group personal training for adults 40+ in Naples",
            "cta_primary": "Start Today",
            "cta_secondary": "Learn More"
        },
        "about": {
            "title": "About Project Evolve",
            "story": "Founded with a mission to make fitness accessible and effective for everyone.",
            "mission": "Helping adults 40+ build strength and confidence.",
            "founder_bio": "Jake Raleigh started Project Evolve to create a supportive fitness community."
        },
        "services": [
            {
                "name": "Personal Training",
                "description": "One-on-one coaching tailored to your goals",
                "benefits": ["Customized workouts", "Nutrition guidance", "Weekly check-ins"],
                "icon_suggestion": "user"
            }
        ],
        "testimonials": [
            {
                "quote": "Project Evolve changed my life. I'm stronger at 50 than I was at 30!",
                "author": "Sarah M.",
                "title": "Member since 2023"
            }
        ],
        "contact": {
            "title": "Ready to Start?",
            "subtitle": "Book your free consultation today",
            "cta": "Get Started"
        },
        "seo": {
            "title": "Project Evolve | Personal Training Naples FL",
            "description": "Small-group personal training for adults 40+ in Naples, Florida.",
            "keywords": ["personal training", "naples fl", "fitness", "gym"]
        },
        "footer_tagline": "Strength. Guidance. Community."
    }

    files = build_site(sample_research, sample_content, "./test_output")
    print(f"Generated files: {files}")
