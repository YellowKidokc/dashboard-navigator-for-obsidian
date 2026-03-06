"""
Enhanced Screenshot Exporter with Smart Naming and Media Sync
Auto-organizes PNGs by date in O:\00_MEDIA\Dashboards\YYYY-MM-DD\
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import asyncio
import shutil
from datetime import datetime


class ScreenshotExporter:
    """
    Export HTML dashboards to PNG with smart naming.
    Auto-syncs to O:\00_MEDIA\Dashboards with date-based folders.
    """
    
    # Default settings
    DEFAULT_WIDTH = 2560
    DEFAULT_HEIGHT = 1440
    MEDIA_FOLDER = Path("O:/00_MEDIA/Dashboards")
    
    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        media_folder: Optional[Path] = None,
        use_date_folders: bool = True
    ):
        self.width = width
        self.height = height
        self.media_folder = Path(media_folder) if media_folder else self.MEDIA_FOLDER
        self.use_date_folders = use_date_folders
        self._playwright_available = self._check_playwright()
    
    def _check_playwright(self) -> bool:
        """Check if Playwright is installed."""
        try:
            from playwright.sync_api import sync_playwright
            return True
        except ImportError:
            print("⚠️  Playwright not installed. Install with:")
            print("   pip install playwright")
            print("   playwright install chromium")
            return False
    
    def _get_dated_folder(self, base_folder: Path) -> Path:
        """Get date-based subfolder (YYYY-MM-DD)."""
        if not self.use_date_folders:
            return base_folder
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        dated_folder = base_folder / date_str
        dated_folder.mkdir(parents=True, exist_ok=True)
        return dated_folder
    
    def _generate_filename(
        self,
        prefix: str,
        chart_type: Optional[str] = None,
        timestamp: bool = False
    ) -> str:
        """
        Generate descriptive filename.
        
        Examples:
            - Primary_Framework_2024-12-26_14-30.png
            - Theory_Comparison_metrics_2024-12-26.png
            - CDCM_Analysis_full_dashboard.png
        """
        parts = [prefix.replace(' ', '_')]
        
        if chart_type:
            parts.append(chart_type)
        
        if timestamp:
            time_str = datetime.now().strftime('%H-%M')
            date_str = datetime.now().strftime('%Y-%m-%d')
            parts.append(f"{date_str}_{time_str}")
        elif self.use_date_folders:
            # Date is in folder name, just add type
            pass
        else:
            # No date folder, add date to filename
            date_str = datetime.now().strftime('%Y-%m-%d')
            parts.append(date_str)
        
        return '_'.join(parts) + '.png'
    
    async def _capture_screenshot_async(
        self,
        html_path: Path,
        output_path: Path,
        wait_for_charts: bool = True
    ) -> bool:
        """Async capture using Playwright."""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(
                    viewport={'width': self.width, 'height': self.height}
                )
                
                # Load HTML file
                await page.goto(f'file:///{html_path.as_posix()}')
                
                # Wait for Chart.js to render
                if wait_for_charts:
                    await page.wait_for_timeout(2000)  # 2 seconds for charts
                    try:
                        await page.wait_for_selector('canvas', state='attached', timeout=5000)
                    except:
                        pass  # No charts, that's OK
                
                # Take screenshot
                await page.screenshot(
                    path=str(output_path),
                    full_page=True,
                    type='png'
                )
                
                await browser.close()
                return True
                
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
            return False
    
    def capture_screenshot(
        self,
        html_path: Path,
        output_path: Path,
        wait_for_charts: bool = True
    ) -> bool:
        """Synchronous wrapper for screenshot capture."""
        if not self._playwright_available:
            return False
        
        return asyncio.run(
            self._capture_screenshot_async(html_path, output_path, wait_for_charts)
        )
    
    def export_dashboard(
        self,
        html_path: Path,
        output_dir: Path,
        filename_prefix: Optional[str] = None,
        chart_type: Optional[str] = None,
        sync_to_media: bool = True
    ) -> Optional[Path]:
        """
        Export dashboard HTML to PNG with smart naming.
        
        Args:
            html_path: Path to HTML dashboard file
            output_dir: Directory to save PNG (local)
            filename_prefix: Optional prefix for output filename
            chart_type: Type of chart (metrics, radar, comparison, etc.)
            sync_to_media: Whether to sync to O:\00_MEDIA\Dashboards
            
        Returns:
            Path to generated PNG or None if failed
        """
        if not self._playwright_available:
            print("Cannot export PNG - Playwright not available")
            return None
        
        if not html_path.exists():
            print(f"HTML file not found: {html_path}")
            return None
        
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if not filename_prefix:
            filename_prefix = html_path.stem
        
        filename = self._generate_filename(filename_prefix, chart_type)
        output_path = output_dir / filename
        
        print(f"📸 Capturing screenshot...")
        print(f"   Source: {html_path.name}")
        print(f"   Output: {output_path.name}")
        
        success = self.capture_screenshot(html_path, output_path)
        
        if success:
            print(f"✓ Screenshot saved: {output_path}")
            
            # Sync to media folder
            if sync_to_media:
                media_path = self._sync_to_media(output_path, filename)
                if media_path:
                    print(f"📁 Media copy: {media_path.relative_to(self.media_folder.parent)}")
            
            return output_path
        else:
            print(f"✗ Screenshot failed")
            return None
    
    def _sync_to_media(self, png_path: Path, filename: str) -> Optional[Path]:
        """Copy PNG to media folder with date organization."""
        try:
            # Get dated subfolder
            target_dir = self._get_dated_folder(self.media_folder)
            target_path = target_dir / filename
            
            # Copy file
            shutil.copy2(png_path, target_path)
            
            return target_path
            
        except Exception as e:
            print(f"⚠️  Media sync failed: {e}")
            return None
    
    def export_multiple(
        self,
        html_files: list[Path],
        output_dir: Path,
        prefix_mapping: Optional[dict] = None
    ) -> list[Path]:
        """
        Export multiple HTML dashboards to PNG.
        
        Args:
            html_files: List of HTML file paths
            output_dir: Directory to save PNGs
            prefix_mapping: Optional dict mapping html_path to prefix name
            
        Returns:
            List of successfully generated PNG paths
        """
        if not self._playwright_available:
            print("Cannot export PNGs - Playwright not available")
            return []
        
        results = []
        
        for html_file in html_files:
            prefix = None
            if prefix_mapping and html_file in prefix_mapping:
                prefix = prefix_mapping[html_file]
            
            png_path = self.export_dashboard(html_file, output_dir, prefix)
            if png_path:
                results.append(png_path)
        
        print(f"\n✓ Exported {len(results)}/{len(html_files)} dashboards to PNG")
        
        return results
    
    def list_media_exports(self, days: int = 7) -> list[Path]:
        """List recent PNG exports in media folder."""
        if not self.media_folder.exists():
            return []
        
        pngs = []
        cutoff = datetime.now().timestamp() - (days * 86400)
        
        for png in self.media_folder.rglob('*.png'):
            if png.stat().st_mtime > cutoff:
                pngs.append(png)
        
        return sorted(pngs, key=lambda p: p.stat().st_mtime, reverse=True)


# === CONVENIENCE FUNCTIONS ===

def export_dashboard_png(
    html_path: Path | str,
    output_dir: Path | str,
    filename_prefix: Optional[str] = None,
    chart_type: Optional[str] = None,
    sync_to_media: bool = True
) -> Optional[Path]:
    """
    Convenience function to export dashboard to PNG.
    
    Auto-syncs to O:\00_MEDIA\Dashboards\YYYY-MM-DD\
    
    Example:
        png_path = export_dashboard_png(
            "dashboard.html",
            "O:/dashboards/images",
            filename_prefix="Primary_Framework",
            chart_type="metrics"
        )
        
        # Creates:
        # O:/dashboards/images/Primary_Framework_metrics.png
        # O:/00_MEDIA/Dashboards/2024-12-26/Primary_Framework_metrics.png
    """
    exporter = ScreenshotExporter()
    return exporter.export_dashboard(
        Path(html_path),
        Path(output_dir),
        filename_prefix,
        chart_type,
        sync_to_media
    )


def check_playwright_installed() -> bool:
    """Check if Playwright is properly installed."""
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright is installed")
        
        # Test chromium availability
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✓ Chromium browser is available")
                return True
            except Exception as e:
                print(f"✗ Chromium not available: {e}")
                print("\nRun: playwright install chromium")
                return False
                
    except ImportError:
        print("✗ Playwright not installed")
        print("\nInstall with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return False


def list_recent_dashboards(days: int = 7):
    """List recent dashboard PNGs in media folder."""
    exporter = ScreenshotExporter()
    pngs = exporter.list_media_exports(days)
    
    if pngs:
        print(f"\n📁 Recent dashboard PNGs (last {days} days):")
        for png in pngs:
            size_mb = png.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(png.stat().st_mtime)
            rel_path = png.relative_to(exporter.media_folder)
            print(f"  • {rel_path} ({size_mb:.1f} MB) - {mtime.strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"\n📁 No dashboard PNGs found in last {days} days")


if __name__ == "__main__":
    # Test script
    print("=" * 70)
    print("PNG SCREENSHOT EXPORTER TEST")
    print("=" * 70)
    
    print("\n[1/3] Checking Playwright installation...")
    if check_playwright_installed():
        print("\n[2/3] Media folder configuration...")
        exporter = ScreenshotExporter()
        print(f"✓ Media folder: {exporter.media_folder}")
        print(f"✓ Date folders: {'Enabled' if exporter.use_date_folders else 'Disabled'}")
        
        print("\n[3/3] Recent exports...")
        list_recent_dashboards(days=7)
        
        print("\n✓ Ready to export dashboards to PNG")
        print("\nUsage:")
        print("  from core.coherence.screenshot_exporter import export_dashboard_png")
        print("  png = export_dashboard_png('dashboard.html', 'output_folder')")
        print("\n  Output locations:")
        print("    • Local: output_folder/Primary_Framework_metrics.png")
        print("    • Media: O:/00_MEDIA/Dashboards/2024-12-26/Primary_Framework_metrics.png")
    else:
        print("\n[2/3] Install Playwright to enable PNG export")
        print("\nRun:")
        print("  pip install playwright")
        print("  playwright install chromium")
