#!/usr/bin/env python3
"""
FastMCP Server implementation for PowerPoint Translator
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP
from ppt_translator.config import Config
from ppt_translator.ppt_handler import PowerPointTranslator
from ppt_translator.post_processing import PowerPointPostProcessor
from ppt_translator.cache import build_cache
from ppt_translator.glossary import find_default_glossary, get_glossary_for_language, load_glossary
from ppt_translator.pricing import estimate_cost, estimate_tokens


def _resolve_glossary_for_mcp(glossary_file: Optional[str], target_language: str):
    """Resolve glossary (explicit or auto-discover ./glossary.yaml) for MCP tools."""
    path = glossary_file
    if not path:
        default = find_default_glossary()
        if default is not None:
            path = str(default)
    glossary_map = load_glossary(path) if path else {}
    return get_glossary_for_language(glossary_map, target_language)


def _dry_run_report(translator: PowerPointTranslator, input_path: Path,
                    target_language: str, model_id: str,
                    slide_numbers: Optional[list] = None,
                    detect_source: bool = True) -> str:
    stats = translator.collect_all_texts(str(input_path), slide_numbers=slide_numbers,
                                         detect_source=detect_source)
    src_lang = stats.get('source_language') or 'en'
    tokens_in = estimate_tokens(stats['total_chars'], src_lang)
    tokens_out = estimate_tokens(stats['total_chars'], target_language)
    cost = estimate_cost(tokens_in, tokens_out, model_id)
    cost_line = f"${cost:.4f}" if cost > 0 else "(pricing unavailable for this model)"
    same_lang = src_lang and src_lang.split('-')[0].lower() == target_language.split('-')[0].lower()
    body = (
        f"📊 Dry-Run Report: {input_path} → {target_language}\n"
        f"  Source language:     {stats.get('source_language') or '(not detected)'}\n"
        f"  Total slides:        {stats['slide_count']}\n"
        f"  Translatable items:  {stats['translatable_items']}\n"
        f"  Total characters:    {stats['total_chars']:,}\n"
    )
    if same_lang:
        body += (f"\n⏭️  Source '{src_lang}' already matches target '{target_language}'. "
                 "No API calls would be made.\n")
    else:
        body += (
            f"\n💰 Cost Estimate ({model_id}):\n"
            f"  Input tokens (est.):  ~{tokens_in:,}\n"
            f"  Output tokens (est.): ~{tokens_out:,}\n"
            f"  Estimated cost:       {cost_line}\n"
        )
    body += "\nℹ️  Run with dry_run=False to perform actual translation."
    return body

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("PowerPoint Translator")

def validate_input_path(input_file: str) -> tuple[Path, str]:
    """
    Validate input file path, handling both absolute and relative paths.
    
    Args:
        input_file: Input file path (absolute or relative)
    
    Returns:
        Tuple of (validated_path, error_message). If error_message is not empty, path validation failed.
    """
    input_path = Path(input_file)
    
    # If it's a relative path, try to resolve it from current working directory
    if not input_path.is_absolute():
        # Try current working directory first
        cwd_path = Path.cwd() / input_file
        if cwd_path.exists():
            input_path = cwd_path
        else:
            # Try the script's directory as fallback
            script_dir = Path(__file__).parent
            script_path = script_dir / input_file
            if script_path.exists():
                input_path = script_path
    
    if not input_path.exists():
        # Provide more helpful error message with current working directory info
        cwd = Path.cwd()
        script_dir = Path(__file__).parent
        error_msg = f"""❌ Error: File not found: {input_file}
📁 Current working directory: {cwd}
📁 Script directory: {script_dir}
💡 Tried paths:
   • {input_file} (as provided)
   • {cwd / input_file} (from current directory)
   • {script_dir / input_file} (from script directory)
💡 Try using absolute path or ensure file is in one of these directories"""
        return input_path, error_msg
    
    if not input_path.suffix.lower() == '.pptx':
        return input_path, f"❌ Error: File must be a PowerPoint (.pptx) file: {input_file}"
    
    return input_path, ""

@mcp.tool()
def translate_powerpoint(
    input_file: str,
    target_language: str = Config.DEFAULT_TARGET_LANGUAGE,
    output_file: Optional[str] = None,
    model_id: str = Config.DEFAULT_MODEL_ID,
    enable_polishing: bool = True,
    glossary_file: Optional[str] = None,
    cache_backend: str = "sqlite",
    dry_run: bool = False,
    translate_charts: bool = True,
    source_language: Optional[str] = None,
    auto_detect_source: bool = True,
) -> str:
    """
    Translate a PowerPoint presentation to the specified language.

    Args:
        input_file: Path to the input PowerPoint file (.pptx)
        target_language: Target language code (e.g., 'ko', 'ja', 'es', 'fr', 'de')
        output_file: Path to save the translated file (optional, auto-generated if not provided)
        model_id: AWS Bedrock model ID to use for translation
        enable_polishing: Enable natural language polishing for more fluent translation
        glossary_file: Path to a glossary YAML file (defaults to ./glossary.yaml if present)
        cache_backend: Translation cache backend: 'sqlite' (default), 'memory', or 'none'
        dry_run: If True, estimate cost without translating or saving the output file
        translate_charts: If True, translate chart titles, axes, categories, and series names

    Returns:
        Success message with translation details (or dry-run report if dry_run=True)
    """
    try:
        # Validate input file using helper function
        input_path, error_msg = validate_input_path(input_file)
        if error_msg:
            return error_msg

        # Validate target language
        if target_language not in Config.LANGUAGE_MAP:
            available_langs = ', '.join(Config.LANGUAGE_MAP.keys())
            return f"❌ Error: Unsupported language '{target_language}'. Available: {available_langs}"

        glossary = _resolve_glossary_for_mcp(glossary_file, target_language)

        # Dry-run path: collect stats without calling Bedrock.
        if dry_run:
            translator = PowerPointTranslator(model_id, enable_polishing,
                                              glossary=glossary, translate_charts=translate_charts,
                                              source_language=source_language,
                                              auto_detect_source=auto_detect_source)
            return _dry_run_report(translator, input_path, target_language, model_id,
                                   detect_source=auto_detect_source)

        # Generate output filename if not provided
        if not output_file:
            output_file = str(input_path.parent / f"{input_path.stem}_translated_{target_language}{input_path.suffix}")

        logger.info(f"Starting translation: {input_path} -> {target_language}")
        with build_cache(cache_backend) as cache:
            translator = PowerPointTranslator(model_id, enable_polishing,
                                              cache=cache, glossary=glossary,
                                              translate_charts=translate_charts,
                                              source_language=source_language,
                                              auto_detect_source=auto_detect_source)
            result = translator.translate_presentation(str(input_path), output_file, target_language)
        
        # Apply post-processing if enabled
        config = Config()
        post_processing_applied = False
        if config.get_bool('ENABLE_TEXT_AUTOFIT', True):
            try:
                verbose = config.get_bool('DEBUG', False)
                post_processor = PowerPointPostProcessor(config, verbose=verbose)
                # Overwrite the original output file instead of creating a new one
                final_output = post_processor.process_presentation(output_file, output_file)
                post_processing_applied = True
                logger.info("Post-processing applied: Text auto-fitting enabled")
            except Exception as e:
                logger.warning(f"Post-processing failed: {e}")
        
        # Format success message
        lang_name = Config.LANGUAGE_MAP.get(target_language, target_language)
        translation_mode = "Natural/Polished" if enable_polishing else "Literal"
        post_processing_status = "✅ Applied" if post_processing_applied else "⚠️ Skipped"
        
        return f"""✅ PowerPoint translation completed successfully!

📁 Input file: {input_path}
📁 Output file: {output_file}
🌐 Target language: {target_language} ({lang_name})
🎨 Translation mode: {translation_mode}
🤖 Model: {model_id}
📝 Translated texts: {result.translated_count}
📋 Translated notes: {result.translated_notes_count}
📊 Total shapes processed: {result.total_shapes}
🔧 Post-processing: {post_processing_status}

💡 Translation features used:
• Intelligent batch processing for efficiency
• Context-aware translation for coherence
• Unified text frame processing
• Formatting preservation
• {'Natural language polishing for fluent output' if enable_polishing else 'Literal translation for accuracy'}"""
        
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        return f"❌ Translation failed: {str(e)}"

@mcp.tool()
def translate_specific_slides(
    input_file: str,
    slide_numbers: str,
    target_language: str = Config.DEFAULT_TARGET_LANGUAGE,
    output_file: Optional[str] = None,
    model_id: str = Config.DEFAULT_MODEL_ID,
    enable_polishing: bool = True,
    glossary_file: Optional[str] = None,
    cache_backend: str = "sqlite",
    dry_run: bool = False,
    translate_charts: bool = True,
    source_language: Optional[str] = None,
    auto_detect_source: bool = True,
) -> str:
    """
    Translate specific slides in a PowerPoint presentation.
    
    Args:
        input_file: Path to the input PowerPoint file (.pptx)
        slide_numbers: Comma-separated slide numbers to translate (e.g., "1,3,5" or "2-4,7")
        target_language: Target language code (e.g., 'ko', 'ja', 'es', 'fr', 'de')
        output_file: Path to save the translated file (optional, auto-generated if not provided)
        model_id: AWS Bedrock model ID to use for translation
        enable_polishing: Enable natural language polishing for more fluent translation
    
    Returns:
        Success message with translation details
    """
    try:
        # Validate input file using helper function
        input_path, error_msg = validate_input_path(input_file)
        if error_msg:
            return error_msg
        
        # Validate target language
        if target_language not in Config.LANGUAGE_MAP:
            available_langs = ', '.join(Config.LANGUAGE_MAP.keys())
            return f"❌ Error: Unsupported language '{target_language}'. Available: {available_langs}"
        
        # Parse slide numbers
        try:
            slide_list = []
            for part in slide_numbers.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    slide_list.extend(range(start, end + 1))
                else:
                    slide_list.append(int(part))
        except ValueError:
            return f"❌ Error: Invalid slide numbers format. Use comma-separated numbers or ranges (e.g., '1,3,5' or '2-4,7')"

        glossary = _resolve_glossary_for_mcp(glossary_file, target_language)

        if dry_run:
            translator = PowerPointTranslator(model_id, enable_polishing,
                                              glossary=glossary, translate_charts=translate_charts,
                                              source_language=source_language,
                                              auto_detect_source=auto_detect_source)
            return _dry_run_report(translator, input_path, target_language, model_id,
                                   slide_numbers=slide_list,
                                   detect_source=auto_detect_source)

        # Generate output filename if not provided
        if not output_file:
            sorted_slides = sorted(set(slide_list))
            if len(sorted_slides) > 1 and sorted_slides[-1] - sorted_slides[0] == len(sorted_slides) - 1:
                slides_suffix = f"_slides_range_{sorted_slides[0]}_{sorted_slides[-1]}"
            else:
                slides_suffix = f"_slides_{'_'.join(map(str, sorted_slides))}"
            output_file = str(input_path.parent / f"{input_path.stem}_translated_{target_language}{slides_suffix}{input_path.suffix}")

        logger.info(f"Starting specific slides translation: {input_path} -> {target_language}")
        with build_cache(cache_backend) as cache:
            translator = PowerPointTranslator(model_id, enable_polishing,
                                              cache=cache, glossary=glossary,
                                              translate_charts=translate_charts,
                                              source_language=source_language,
                                              auto_detect_source=auto_detect_source)
            result = translator.translate_specific_slides(str(input_path), output_file, target_language, slide_list)
        
        # Check for errors
        if result.errors:
            return f"❌ Translation failed: {'; '.join(result.errors)}"
        
        # Apply post-processing if enabled
        config = Config()
        post_processing_applied = False
        if config.get_bool('ENABLE_TEXT_AUTOFIT', True):
            try:
                verbose = config.get_bool('DEBUG', False)
                post_processor = PowerPointPostProcessor(config, verbose=verbose)
                # Overwrite the original output file instead of creating a new one
                final_output = post_processor.process_presentation(output_file, output_file)
                post_processing_applied = True
                logger.info("Post-processing applied: Text auto-fitting enabled")
            except Exception as e:
                logger.warning(f"Post-processing failed: {e}")
        
        # Format success message
        lang_name = Config.LANGUAGE_MAP.get(target_language, target_language)
        translation_mode = "Natural/Polished" if enable_polishing else "Literal"
        post_processing_status = "✅ Applied" if post_processing_applied else "⚠️ Skipped"
        
        return f"""✅ Specific slides translation completed successfully!

📁 Input file: {input_path}
📁 Output file: {output_file}
📄 Translated slides: {sorted(set(slide_list))}
🌐 Target language: {target_language} ({lang_name})
🎨 Translation mode: {translation_mode}
🤖 Model: {model_id}
📝 Translated texts: {result.translated_count}
📋 Translated notes: {result.translated_notes_count}
📊 Total shapes processed: {result.total_shapes}
🔧 Post-processing: {post_processing_status}

💡 Translation features used:
• Intelligent batch processing for efficiency
• Context-aware translation for coherence
• Unified text frame processing
• Formatting preservation
• {'Natural language polishing for fluent output' if enable_polishing else 'Literal translation for accuracy'}"""
        
    except Exception as e:
        logger.error(f"Specific slides translation failed: {str(e)}")
        return f"❌ Translation failed: {str(e)}"

@mcp.tool()
def get_slide_info(input_file: str) -> str:
    """
    Get information about slides in a PowerPoint presentation.
    
    Args:
        input_file: Path to the PowerPoint file (.pptx)
    
    Returns:
        Information about the presentation including slide count and preview of each slide
    """
    try:
        # Validate input file using helper function
        input_path, error_msg = validate_input_path(input_file)
        if error_msg:
            return error_msg
        
        # Create translator to access slide info methods
        translator = PowerPointTranslator()
        slide_count = translator.get_slide_count(str(input_path))
        
        info_text = f"""📊 PowerPoint Presentation Information

📁 File: {input_path}
📄 Total slides: {slide_count}

📋 Slide previews:
"""
        
        # Get preview for each slide (limit to first 10 slides for readability)
        max_preview_slides = min(slide_count, 10)
        for i in range(1, max_preview_slides + 1):
            try:
                preview = translator.get_slide_preview(str(input_path), i, max_chars=150)
                info_text += f"\n🔸 Slide {i}: {preview}"
            except Exception as e:
                info_text += f"\n🔸 Slide {i}: [Error getting preview: {str(e)}]"
        
        if slide_count > 10:
            info_text += f"\n\n... and {slide_count - 10} more slides"
        
        info_text += f"""

💡 Usage examples:
• Translate all slides: translate_powerpoint("{input_file}")
• Translate specific slides: translate_specific_slides("{input_file}", "1,3,5")
• Translate slide range: translate_specific_slides("{input_file}", "2-4")"""
        
        return info_text
        
    except Exception as e:
        logger.error(f"Failed to get slide info: {str(e)}")
        return f"❌ Failed to get slide info: {str(e)}"

@mcp.tool()
def get_slide_preview(input_file: str, slide_number: int) -> str:
    """
    Get a detailed preview of a specific slide's content.
    
    Args:
        input_file: Path to the PowerPoint file (.pptx)
        slide_number: Slide number to preview (1-based indexing)
    
    Returns:
        Detailed preview of the slide content
    """
    try:
        # Validate input file using helper function
        input_path, error_msg = validate_input_path(input_file)
        if error_msg:
            return error_msg
        
        # Create translator and get preview
        translator = PowerPointTranslator()
        slide_count = translator.get_slide_count(str(input_path))
        
        if slide_number < 1 or slide_number > slide_count:
            return f"❌ Error: Invalid slide number {slide_number}. Valid range: 1-{slide_count}"
        
        preview = translator.get_slide_preview(str(input_path), slide_number, max_chars=500)
        
        return f"""📄 Slide {slide_number} Preview

📁 File: {input_path}
📊 Total slides: {slide_count}

📝 Content preview:
{preview}

💡 To translate this slide:
translate_specific_slides("{input_file}", "{slide_number}")"""
        
    except Exception as e:
        logger.error(f"Failed to get slide preview: {str(e)}")
        return f"❌ Failed to get slide preview: {str(e)}"

@mcp.tool()
def list_supported_languages() -> str:
    """
    List all supported target languages for translation.
    
    Returns:
        List of supported language codes and names
    """
    languages_text = "🌐 Supported target languages:\n\n"
    for code, name in sorted(Config.LANGUAGE_MAP.items()):
        languages_text += f"• {code}: {name}\n"
    
    return languages_text

@mcp.tool()
def list_supported_models() -> str:
    """
    List all supported AWS Bedrock models for translation.
    
    Returns:
        List of supported model IDs
    """
    models_text = "🤖 Supported AWS Bedrock models:\n\n"
    for model in Config.SUPPORTED_MODELS:
        models_text += f"• {model}\n"
    
    return models_text


@mcp.tool()
def get_translation_help() -> str:
    """
    Get help information about using the PowerPoint translator.
    
    Returns:
        Help text with usage examples
    """
    return """📖 PowerPoint Translator Help

🎯 Main Functions:
• translate_powerpoint() - Translate entire PowerPoint presentation
• translate_specific_slides() - Translate only specific slides
• batch_translate_powerpoint() - Translate all PowerPoint files in a folder
• get_slide_info() - Get presentation overview and slide previews
• get_slide_preview() - Get detailed preview of a specific slide

📋 Required Parameters:
• input_file: Path to your .pptx file
• input_folder: Path to folder containing .pptx files (for batch)

🔧 Optional Parameters:
• target_language: Language code (default: 'ko' for Korean)
• output_file/output_folder: Output path (auto-generated if not specified)
• model_id: Bedrock model (default: Claude Sonnet 4.6)
• enable_polishing: Natural translation vs literal (default: true)
• recursive: Process subfolders (default: true, for batch only)
• workers: Parallel workers (default: 4, for batch only)

💡 Usage Examples:

1. Get presentation information:
   get_slide_info("presentation.pptx")

2. Preview specific slide:
   get_slide_preview("presentation.pptx", 3)

3. Translate entire presentation:
   translate_powerpoint("presentation.pptx")

4. Translate specific slides (individual):
   translate_specific_slides("slides.pptx", "1,3,5")

5. Translate slide range:
   translate_specific_slides("slides.pptx", "2-4")

6. Translate mixed (individual + range):
   translate_specific_slides("slides.pptx", "1,3-5,8")

7. Batch translate folder (includes subfolders by default):
   batch_translate_powerpoint("presentations/")

8. Batch translate top level only (disable recursion):
   batch_translate_powerpoint("presentations/", recursive=False)

9. Batch translate to Spanish with custom output:
   batch_translate_powerpoint("input/", "es", "output/")

10. Translate to Spanish with custom output:
    translate_specific_slides("slides.pptx", "1-3", "es", "spanish_slides.pptx")

11. Literal translation (no polishing):
    translate_specific_slides("doc.pptx", "2,4", "ja", enable_polishing=False)

🌐 Get supported languages:
   list_supported_languages()

🤖 Get supported models:
   list_supported_models()

⚙️ Configuration:
• AWS credentials must be configured (aws configure)
• Bedrock access required in your AWS account
• Supported file format: .pptx only

📄 Slide Number Format:
• Individual slides: "1,3,5"
• Ranges: "2-4" (translates slides 2, 3, 4)
• Mixed: "1,3-5,8" (translates slides 1, 3, 4, 5, 8)

📁 Batch Processing:
• Non-recursive: Only files in the specified folder
• Recursive: Files in all subfolders (like reInvent-2025/session1/, session2/, etc.)
• Preserves folder structure in output
• Parallel processing for efficiency"""


@mcp.tool()
def batch_translate_powerpoint(
    input_folder: str,
    target_language: str = Config.DEFAULT_TARGET_LANGUAGE,
    output_folder: Optional[str] = None,
    model_id: str = Config.DEFAULT_MODEL_ID,
    enable_polishing: bool = True,
    recursive: bool = True,
    workers: int = 4,
    glossary_file: Optional[str] = None,
    cache_backend: str = "sqlite",
    cache_path: Optional[str] = None,
    dry_run: bool = False,
    translate_charts: bool = True,
    source_language: Optional[str] = None,
    auto_detect_source: bool = True,
) -> str:
    """
    Translate all PowerPoint files in a folder (with optional recursive processing).

    Args:
        input_folder: Path to the input folder containing PowerPoint files
        target_language: Target language code (e.g., 'ko', 'ja', 'es', 'fr', 'de')
        output_folder: Path to save translated files (optional, auto-generated if not provided)
        model_id: AWS Bedrock model ID to use for translation
        enable_polishing: Enable natural language polishing for more fluent translation
        recursive: Process subfolders recursively (default: True — set to False to limit to top level)
        workers: Number of parallel workers (default: 4)
        glossary_file: Path to a glossary YAML file (defaults to ./glossary.yaml if present)
        cache_backend: Translation cache backend: 'sqlite' (default), 'memory', or 'none'
        cache_path: SQLite cache path (ignored for memory/none backends)
        dry_run: If True, estimate aggregate cost without translating
        translate_charts: If True, translate chart titles/axes/categories/series

    Returns:
        Success message with batch translation details
    """
    try:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        # Reuse the module-level worker from the CLI so ProcessPoolExecutor can
        # pickle it — an inner function can't be pickled across fork/spawn.
        from ppt_translator.cli import _translate_single_file

        input_path = Path(input_folder)
        if not input_path.exists() or not input_path.is_dir():
            return f"❌ Error: Input folder not found or not a directory: {input_folder}"

        if target_language not in Config.LANGUAGE_MAP:
            available_langs = ', '.join(Config.LANGUAGE_MAP.keys())
            return f"❌ Error: Unsupported language '{target_language}'. Available: {available_langs}"

        output_path = Path(output_folder) if output_folder else input_path / f"translated_{target_language}"
        output_path.mkdir(parents=True, exist_ok=True)

        if recursive:
            ppt_files = list(input_path.rglob("*.pptx")) + list(input_path.rglob("*.ppt"))
        else:
            ppt_files = list(input_path.glob("*.pptx")) + list(input_path.glob("*.ppt"))

        if not ppt_files:
            search_type = "recursively" if recursive else ""
            return f"❌ No PowerPoint files found {search_type} in {input_folder}"

        # Resolve glossary once so every worker loads the same file.
        resolved_glossary_path = glossary_file
        if resolved_glossary_path is None:
            default = find_default_glossary()
            if default is not None:
                resolved_glossary_path = str(default)

        if dry_run:
            glossary = _resolve_glossary_for_mcp(glossary_file, target_language)
            total_chars = 0
            total_items = 0
            translator = PowerPointTranslator(model_id, enable_polishing,
                                              glossary=glossary, translate_charts=translate_charts,
                                              source_language=source_language,
                                              auto_detect_source=auto_detect_source)
            for ppt_file in ppt_files:
                stats = translator.collect_all_texts(
                    str(ppt_file),
                    detect_source=auto_detect_source and translator.source_language is None,
                )
                total_chars += stats['total_chars']
                total_items += stats['translatable_items']
                if translator.source_language is None and stats.get('source_language'):
                    translator.source_language = stats['source_language']
                    translator.engine.source_language = stats['source_language']
            src_for_estimate = translator.source_language or source_language or 'en'
            tokens_in = estimate_tokens(total_chars, src_for_estimate)
            tokens_out = estimate_tokens(total_chars, target_language)
            cost = estimate_cost(tokens_in, tokens_out, model_id)
            cost_line = f"${cost:.4f}" if cost > 0 else "(pricing unavailable for this model)"
            return (
                f"📊 Batch Dry-Run Report\n"
                f"  Source language:     {translator.source_language or '(not detected)'}\n"
                f"  Files:               {len(ppt_files)}\n"
                f"  Translatable items:  {total_items}\n"
                f"  Total characters:    {total_chars:,}\n"
                f"  Input tokens (est.): ~{tokens_in:,}\n"
                f"  Output tokens (est.):~{tokens_out:,}\n"
                f"  Estimated cost:      {cost_line}\n"
            )

        # Prepare tasks with relative path preservation
        tasks = []
        for ppt_file in ppt_files:
            relative_path = ppt_file.relative_to(input_path)
            output_file = output_path / relative_path.parent / f"{relative_path.stem}_{target_language}{relative_path.suffix}"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            tasks.append((
                ppt_file, output_file, target_language, model_id, enable_polishing,
                cache_backend, cache_path or str(Path.home() / '.ppt-translator' / 'cache.db'),
                resolved_glossary_path, translate_charts,
                source_language, auto_detect_source,
            ))

        success_count = 0
        failed_files = []

        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_translate_single_file, task): task for task in tasks}
            for future in as_completed(futures):
                filename, output_name, result, error = future.result()
                if result:
                    success_count += 1
                else:
                    failed_files.append(f"{filename}: {error}" if error else filename)
        
        # Format results
        lang_name = Config.LANGUAGE_MAP.get(target_language, target_language)
        translation_mode = "Natural/Polished" if enable_polishing else "Literal"
        
        result_text = f"""✅ Batch PowerPoint translation completed!

📁 Input folder: {input_path}
📁 Output folder: {output_path}
🔄 Recursive mode: {'ON' if recursive else 'OFF'}
🌐 Target language: {target_language} ({lang_name})
🎨 Translation mode: {translation_mode}
🤖 Model: {model_id}
⚡ Workers: {workers}

📊 Results:
• Total files found: {len(ppt_files)}
• Successfully translated: {success_count}
• Failed: {len(failed_files)}"""

        if failed_files:
            result_text += "\n\n❌ Failed files:\n"
            for failed in failed_files[:5]:  # Show first 5 failures
                result_text += f"• {failed}\n"
            if len(failed_files) > 5:
                result_text += f"... and {len(failed_files) - 5} more"
        
        return result_text
        
    except Exception as e:
        logger.error(f"Batch translation failed: {str(e)}")
        return f"❌ Batch translation failed: {str(e)}"

@mcp.tool()
def post_process_powerpoint(
    input_file: str,
    output_file: Optional[str] = None,
    text_threshold: Optional[int] = None,
    enable_autofit: bool = True
) -> str:
    """
    Apply post-processing to a PowerPoint presentation to optimize text boxes.
    
    This function enables text wrapping and shrink text on overflow for text boxes
    that contain text longer than the specified threshold.
    
    Args:
        input_file: Path to the input PowerPoint file (.pptx)
        output_file: Path to save the processed file (optional, auto-generated if not provided)
        text_threshold: Text length threshold for enabling auto-fit (overrides .env setting)
        enable_autofit: Enable text auto-fitting (default: True)
    
    Returns:
        Success message with post-processing details
    """
    try:
        # Validate input file using helper function
        input_path, error_msg = validate_input_path(input_file)
        if error_msg:
            return error_msg
        
        # Create configuration
        config = Config()
        if text_threshold is not None:
            config.set('TEXT_LENGTH_THRESHOLD', str(text_threshold))
        if not enable_autofit:
            config.set('ENABLE_TEXT_AUTOFIT', 'false')
        
        # Generate output filename if not provided
        if not output_file:
            output_file = str(input_path)  # Overwrite the original file
        
        # Apply post-processing
        logger.info(f"Starting post-processing: {input_path}")
        verbose = config.get_bool('DEBUG', False)
        post_processor = PowerPointPostProcessor(config, verbose=verbose)
        final_output = post_processor.process_presentation(str(input_path), output_file)
        
        threshold = config.get_int('TEXT_LENGTH_THRESHOLD', 10)
        autofit_enabled = config.get_bool('ENABLE_TEXT_AUTOFIT', True)
        
        return f"""✅ PowerPoint post-processing completed successfully!

📁 Input file: {input_path}
📁 Output file: {final_output}
🔧 Text auto-fitting: {'✅ Enabled' if autofit_enabled else '❌ Disabled'}
📏 Text length threshold: {threshold} characters
📝 Processing applied to text boxes longer than {threshold} characters

💡 Post-processing features applied:
• Text wrapping in shape enabled
• Shrink text on overflow enabled
• Text box margins optimized
• Formatting preservation maintained"""
        
    except Exception as e:
        logger.error(f"Post-processing failed: {str(e)}")
        return f"❌ Post-processing failed: {str(e)}"


def main():
    """Main entry point for the FastMCP server."""
    # Run the FastMCP server
    mcp.run()

if __name__ == "__main__":
    main()
