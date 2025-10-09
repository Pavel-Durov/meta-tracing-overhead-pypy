#!/usr/bin/env python3
"""
PyPy Meta-Tracing JIT Overhead Analysis CLI

Command-line interface for collecting benchmark data and generating plots
to analyze PyPy's meta-tracing JIT overhead.

Based on Carl Friedrich Bolz-Tereick's blog post:
https://cfbolz.de/posts/speed-of-tracing/
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import click
import json


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    PyPy Meta-Tracing JIT Overhead Analysis Tool

    Measure and visualize the overhead of PyPy's meta-tracing interpreter.
    """
    pass


@cli.command()
@click.option('--start', default=1, type=int, help='Starting iteration count')
@click.option('--end', default=20000, type=int, help='Ending iteration count')
@click.option('--step', default=1, type=int, help='Step size between iterations')
@click.option('--skip-cpython', is_flag=True, help='Skip CPython baseline collection')
@click.option('--force', is_flag=True, help='Overwrite existing data files without prompting')
@click.option('--pypy-path', default='pypy', help='Path to PyPy executable')
@click.option('--python-path', default='python3', help='Path to CPython executable')
@click.option('--output-dir', default=None, type=click.Path(), help='Output directory (default: results/YYYY-MM-DD_HH-MM-SS)')
def collect(start, end, step, skip_cpython, force, pypy_path, python_path, output_dir):
    """
    Collect benchmark data for JIT overhead analysis.

    Runs the benchmark with PyPy (JIT enabled and disabled) and optionally CPython
    to generate data for comparing execution times across different iteration counts.
    """
    click.echo(click.style("PyPy Meta-Tracing JIT Overhead Data Collection", fg='cyan', bold=True))
    click.echo()

    # Check if PyPy is installed
    if not shutil.which(pypy_path):
        click.echo(click.style(f"Error: PyPy not found at '{pypy_path}'", fg='red'))
        click.echo("Please install PyPy or specify the correct path with --pypy-path")
        click.echo("Visit: https://www.pypy.org/download.html")
        sys.exit(1)

    # Show PyPy version
    try:
        result = subprocess.run([pypy_path, '--version'],
                              capture_output=True, text=True, check=True)
        click.echo(f"PyPy version: {result.stderr.strip()}")
        click.echo()
    except subprocess.CalledProcessError:
        click.echo(click.style("Warning: Could not determine PyPy version", fg='yellow'))

    # Create results directory with timestamp
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        results_dir = Path('results') / timestamp
    else:
        results_dir = Path(output_dir)

    results_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Results directory: {results_dir}")
    click.echo()

    benchmark_script = 'benchmark.py'
    if not Path(benchmark_script).exists():
        click.echo(click.style(f"Error: {benchmark_script} not found", fg='red'))
        sys.exit(1)

    # Data collection for JIT enabled
    data_jit_path = results_dir / 'data_jit.txt'
    if not _collect_data(
        pypy_path, benchmark_script, data_jit_path,
        start, end, step, force,
        "JIT enabled", []
    ):
        sys.exit(1)

    # Data collection for JIT disabled
    data_nojit_path = results_dir / 'data_nojit.txt'
    if not _collect_data(
        pypy_path, benchmark_script, data_nojit_path,
        start, end, step, force,
        "JIT disabled", ['--jit', 'off']
    ):
        sys.exit(1)

    # Data collection for CPython (optional)
    if not skip_cpython:
        if shutil.which(python_path):
            data_cpython_path = results_dir / 'data_cpython.txt'
            _collect_data(
                python_path, benchmark_script, data_cpython_path,
                start, end, step, force,
                "CPython baseline", []
            )
        else:
            click.echo(click.style(
                f"Warning: CPython not found at '{python_path}'. Skipping baseline.",
                fg='yellow'
            ))
            click.echo()

    click.echo()
    click.echo(click.style("All data collection complete!", fg='green', bold=True))
    click.echo(f"Results saved in {results_dir}/ directory:")
    click.echo(f"  - {data_jit_path.name} (PyPy with JIT)")
    click.echo(f"  - {data_nojit_path.name} (PyPy without JIT)")
    if not skip_cpython and (results_dir / 'data_cpython.txt').exists():
        click.echo(f"  - data_cpython.txt (CPython baseline)")
    click.echo()
    click.echo(f"Run 'python main.py plot --results-dir {results_dir}' to visualize the data.")

    # Return the results directory for use by other commands
    return results_dir


def _collect_data(interpreter_path, script_path, output_path,
                  start, end, step, force, label, extra_args):
    """Helper function to collect benchmark data."""
    click.echo(click.style(f"Collecting data with {label}...", fg='cyan'))
    click.echo(f"Running iterations from {start} to {end} (step={step})...")

    # Check if file exists
    if output_path.exists():
        if force:
            output_path.unlink()
            click.echo(f"Removed existing {output_path.name}")
        else:
            click.echo(click.style(
                f"Warning: {output_path} already exists.", fg='yellow'
            ))
            if not click.confirm("Remove existing file and start fresh?"):
                click.echo("Skipping this data collection.")
                click.echo()
                return True
            output_path.unlink()

    # Run benchmark for each iteration count
    with click.progressbar(
        range(start, end + 1, step),
        label=f'{label:20s}',
        show_eta=True
    ) as bar:
        with open(output_path, 'a') as f:
            for i in bar:
                try:
                    cmd = [interpreter_path, '-S'] + extra_args + [script_path, str(i)]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    f.write(result.stdout)
                    f.flush()
                except subprocess.CalledProcessError as e:
                    click.echo()
                    click.echo(click.style(
                        f"Error running benchmark at iteration {i}: {e}",
                        fg='red'
                    ))
                    return False

    click.echo(click.style(f"{label} data collection complete!", fg='green'))
    click.echo()
    return True


@cli.command()
@click.option('--results-dir', default=None, type=click.Path(exists=True),
              help='Directory containing benchmark data files (default: latest run in results/)')
@click.option('--output-dir', default=None, type=click.Path(),
              help='Directory to save plot images (default: <results-dir>/plots)')
def plot(results_dir, output_dir):
    """
    Generate plots from collected benchmark data.

    Creates visualizations showing execution time, speedup factors,
    and overhead comparisons between different configurations.
    """
    click.echo(click.style("Generating plots from benchmark data...", fg='cyan', bold=True))
    click.echo()

    # Import plot_results module
    try:
        import plot_results
    except ImportError as e:
        click.echo(click.style(f"Error importing plot_results: {e}", fg='red'))
        sys.exit(1)

    # If no results directory specified, find the latest one
    if results_dir is None:
        results_base = Path('results')
        if not results_base.exists():
            click.echo(click.style("Error: No results directory found.", fg='red'))
            click.echo("Please run 'python main.py collect' first.")
            sys.exit(1)

        # Find all timestamped directories
        timestamp_dirs = [d for d in results_base.iterdir()
                         if d.is_dir() and d.name[0].isdigit()]

        if not timestamp_dirs:
            click.echo(click.style("Error: No benchmark runs found in results/", fg='red'))
            click.echo("Please run 'python main.py collect' first.")
            sys.exit(1)

        # Get the most recent directory
        results_path = max(timestamp_dirs, key=lambda d: d.name)
        click.echo(f"Using latest results from: {results_path}")
    else:
        results_path = Path(results_dir)

    click.echo()

    # Check for data files
    data_jit = results_path / 'data_jit.txt'
    data_nojit = results_path / 'data_nojit.txt'
    data_cpython = results_path / 'data_cpython.txt'

    if not data_jit.exists() and not data_nojit.exists():
        click.echo(click.style("Error: No data files found in results directory.", fg='red'))
        click.echo("Please run 'python main.py collect' first to generate benchmark data.")
        sys.exit(1)

    # Load data
    click.echo("Loading benchmark data...")
    data_dict = {
        'PyPy with JIT': plot_results.load_data(str(data_jit)) if data_jit.exists() else None,
        'PyPy without JIT': plot_results.load_data(str(data_nojit)) if data_nojit.exists() else None,
        'CPython': plot_results.load_data(str(data_cpython)) if data_cpython.exists() else None
    }

    # Check if we have any data
    if all(data is None for data in data_dict.values()):
        click.echo(click.style("Error: Could not load any data files.", fg='red'))
        sys.exit(1)

    # Create output directory (default to plots subdirectory in results)
    if output_dir is None:
        output_path = results_path / 'plots'
    else:
        output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    click.echo("Generating plots...")

    # Generate plots
    plot_results.plot_execution_times(data_dict, str(output_path))
    plot_results.plot_speedup(data_dict['PyPy with JIT'],
                             data_dict['PyPy without JIT'],
                             str(output_path))
    plot_results.plot_overhead_ratio(data_dict['PyPy with JIT'],
                                     data_dict['PyPy without JIT'],
                                     data_dict['CPython'],
                                     str(output_path))

    # Calculate and display statistics
    plot_results.calculate_statistics(data_dict)

    click.echo()
    click.echo(click.style("All plots generated successfully!", fg='green', bold=True))
    click.echo(f"Plots saved to {output_path}/")
    click.echo("  - execution_times.png")
    click.echo("  - speedup_factor.png")
    if data_dict['CPython'] is not None:
        click.echo("  - overhead_ratio.png")


@cli.command()
@click.option('--start', default=1, type=int, help='Starting iteration count')
@click.option('--end', default=20000, type=int, help='Ending iteration count')
@click.option('--step', default=1, type=int, help='Step size between iterations')
@click.option('--skip-cpython', is_flag=True, help='Skip CPython baseline collection')
@click.option('--force', is_flag=True, help='Overwrite existing data files without prompting')
@click.option('--pypy-path', default='pypy', help='Path to PyPy executable')
@click.option('--python-path', default='python3', help='Path to CPython executable')
@click.option('--output-dir', default=None, type=click.Path(), help='Output directory (default: results/YYYY-MM-DD_HH-MM-SS)')
def run(start, end, step, skip_cpython, force, pypy_path, python_path, output_dir):
    """
    Run the complete benchmark workflow (collect + plot).

    This command collects benchmark data and then generates plots in one step.
    """
    click.echo(click.style("Running complete benchmark workflow", fg='cyan', bold=True))
    click.echo()

    # Invoke collect
    ctx = click.get_current_context()
    results_dir = ctx.invoke(collect, start=start, end=end, step=step,
                            skip_cpython=skip_cpython, force=force,
                            pypy_path=pypy_path, python_path=python_path,
                            output_dir=output_dir)

    # Construct the config dictionary
    config = {
        'start': start,
        'end': end,
        'step': step,
        'skip_cpython': skip_cpython,
        'force': force,
        'pypy_path': pypy_path,
        'python_path': python_path,
        'output_dir': str(output_dir)
    }

    # Save config to a .config.json file in the results directory
    config_path = results_dir / '.config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

    click.echo(f"Configuration parameters saved to: {config_path}")

    # Invoke plot with the results directory from collect
    ctx.invoke(plot, results_dir=str(results_dir), output_dir=None)


@cli.command()
@click.option('--all', 'remove_all', is_flag=True, help='Remove all benchmark runs')
@click.option('--run-dir', default=None, type=click.Path(exists=True), help='Specific run directory to remove')
def clean(remove_all, run_dir):
    """
    Clean up generated files.

    By default, removes only the latest benchmark run.
    Use --all to remove all runs, or --run-dir to specify a particular run.
    """
    results_base = Path('results')

    if not results_base.exists():
        click.echo("Nothing to clean - results directory does not exist.")
        return

    if remove_all:
        if click.confirm(f"Remove {results_base}/ and all its contents?"):
            shutil.rmtree(results_base)
            click.echo(click.style(f"Removed {results_base}/", fg='green'))
        else:
            click.echo("Cancelled.")
    elif run_dir:
        run_path = Path(run_dir)
        if click.confirm(f"Remove {run_path}/?"):
            shutil.rmtree(run_path)
            click.echo(click.style(f"Removed {run_path}/", fg='green'))
        else:
            click.echo("Cancelled.")
    else:
        # Remove only the latest run
        timestamp_dirs = [d for d in results_base.iterdir()
                         if d.is_dir() and d.name[0].isdigit()]

        if not timestamp_dirs:
            click.echo("No benchmark runs found to clean.")
            return

        latest_dir = max(timestamp_dirs, key=lambda d: d.name)
        if click.confirm(f"Remove latest run at {latest_dir}/?"):
            shutil.rmtree(latest_dir)
            click.echo(click.style(f"Removed {latest_dir}/", fg='green'))
        else:
            click.echo("Cancelled.")


@cli.command()
def list():
    """
    List all benchmark runs in the results directory.
    """
    results_base = Path('results')

    if not results_base.exists():
        click.echo("No results directory found.")
        return

    timestamp_dirs = sorted([d for d in results_base.iterdir()
                            if d.is_dir() and d.name[0].isdigit()],
                           key=lambda d: d.name, reverse=True)

    if not timestamp_dirs:
        click.echo("No benchmark runs found.")
        return

    click.echo(click.style("Available benchmark runs:", fg='cyan', bold=True))
    click.echo()

    for i, run_dir in enumerate(timestamp_dirs):
        # Check what data files exist
        has_jit = (run_dir / 'data_jit.txt').exists()
        has_nojit = (run_dir / 'data_nojit.txt').exists()
        has_cpython = (run_dir / 'data_cpython.txt').exists()
        has_plots = (run_dir / 'plots').exists()

        # Format status
        status_parts = []
        if has_jit:
            status_parts.append('JIT')
        if has_nojit:
            status_parts.append('no-JIT')
        if has_cpython:
            status_parts.append('CPython')

        status = ', '.join(status_parts) if status_parts else 'incomplete'

        marker = '→' if i == 0 else ' '
        latest_marker = click.style(' (latest)', fg='green') if i == 0 else ''
        plots_marker = click.style(' [plots]', fg='blue') if has_plots else ''

        click.echo(f"{marker} {run_dir.name}{latest_marker} - {status}{plots_marker}")

    click.echo()
    click.echo(f"Total runs: {len(timestamp_dirs)}")


if __name__ == '__main__':
    cli()
