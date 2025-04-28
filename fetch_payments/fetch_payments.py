#!/usr/bin/env python3
"""
fetch_payments.py

Ein benutzerfreundliches CLI-Tool zum Abrufen und Anzeigen neuer Stripe-Checkout-Sessions.

Features:
- CLI mit argparse (konfigurierbar: JSON-Pfad, Anzeigeoptionen, Polling-Intervall)
- Umgebungskonfigurierter Stripe-API-Key
- JSON-Persistenz aller Zahlungen
- Übersichtliche Konsolen-Ausgabe mit Rich Tables
- Automatisches Polling in einstellbaren Intervallen
- Logging mit anpassbarem Detailgrad

Installation:
    pip install stripe rich

Beispielaufruf:
    export STRIPE_API_KEY=sk_test_xxx
    python fetch_stripe_payments.py --json payments.json --show-table --verbose --interval 15
"""
import os
import json
import sys
import time
import logging
import argparse
from typing import List, Dict

import stripe
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

# Setup Rich console for styled output
console = Console()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("fetch_stripe_payments")


def load_existing_payments(path: str) -> List[Dict]:
    """Lade bestehende Zahlungen aus einer JSON-Datei."""
    if os.path.isfile(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                logger.info(f"[green]Loaded[/green] {len(data)} existing payments from [bold]{path}[/bold]")
                return data
        except Exception as e:
            logger.warning(f"[yellow]Warning:[/yellow] Could not parse JSON file: {e} — starting fresh.")
    return []


def save_payments(path: str, payments: List[Dict]) -> None:
    """Speichere alle Zahlungen in einer JSON-Datei."""
    try:
        with open(path, 'w') as f:
            json.dump(payments, f, indent=2)
        logger.info(f"[green]Saved[/green] {len(payments)} payments to [bold]{path}[/bold]")
    except Exception as e:
        logger.error(f"[red]Error saving JSON:[/red] {e}")
        sys.exit(1)


def get_last_timestamp(payments: List[Dict]) -> int:
    """Gebe den neuesten Zeitstempel (UNIX) aller bisherigen Zahlungen zurück."""
    if not payments:
        return 0
    return max(p.get('created', 0) for p in payments)


def fetch_new_sessions(since: int) -> List[Dict]:
    """Hole alle neuen Stripe Checkout Sessions seit einem gegebenen Zeitstempel."""
    logger.debug(f"Fetching sessions created after UNIX timestamp {since}...")
    try:
        sessions = stripe.checkout.Session.list(
            limit=100,
            created={'gt': since},
            expand=['data.customer_details']
        )
    except Exception as e:
        logger.error(f"[red]Stripe API Error:[/red] {e}")
        return []

    new_records = []
    for session in sessions.auto_paging_iter():
        cust = session.customer_details or {}
        record = {
            'id': session.id,
            'created': session.created,
            'customer_email': cust.get('email'),
            'customer_name': cust.get('name'),
            'customer_phone': cust.get('phone'),
            'amount_total': session.amount_total / 100.0,
            'currency': session.currency,
            'payment_method_types': session.payment_method_types,
            'payment_status': session.payment_status,
            'locale': session.locale,
            'metadata': session.metadata or {}
        }
        logger.info(
            f"[cyan]New Session:[/cyan] {record['id']} | {record['customer_email']} | "
            f"{record['amount_total']:.2f} {record['currency'].upper()}"
        )
        new_records.append(record)
    return new_records


def display_table(payments: List[Dict]) -> None:
    """Zeige eine tabellarische Übersicht der Zahlungen in der Konsole."""
    table = Table(title="Stripe Payments Summary")
    columns = ["ID", "Email", "Amount", "Currency", "Status", "Created"]
    for col in columns:
        table.add_column(col, justify="center")

    for p in payments:
        table.add_row(
            p['id'],
            p.get('customer_email') or "-",
            f"{p['amount_total']:.2f}",
            p['currency'].upper(),
            p['payment_status'],
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p['created']))
        )
    console.print(table)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch and store Stripe Checkout Session payments."
    )
    parser.add_argument(
        '--json', '-j', default='payments.json',
        help='Pfad zur JSON-Datei zum Speichern der Zahlungen'
    )
    parser.add_argument(
        '--show-table', action='store_true',
        help='Zeige nach dem Abruf eine Übersichtstabelle'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Mehr Ausgaben (Debug-Level Logging)'
    )
    parser.add_argument(
        '--interval', '-i', type=int, default=15,
        help='Polling-Intervall in Sekunden (0 = nur einmal)'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Logging-Level anpassen
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Stripe API-Key aus ENV
    api_key = os.getenv('STRIPE_API_KEY')
    if not api_key:
        console.print("[red]Error:[/red] Environment variable STRIPE_API_KEY is not set.")
        sys.exit(1)
    stripe.api_key = api_key

    # Lade bestehende Zahlungen
    payments = load_existing_payments(args.json)

    # Polling-Schleife
    while True:
        last_ts = get_last_timestamp(payments)
        new_payments = fetch_new_sessions(last_ts)
        if new_payments:
            payments.extend(new_payments)
            payments.sort(key=lambda x: x['created'])
            save_payments(args.json, payments)
            if args.show_table:
                display_table(new_payments)
        else:
            logger.debug("No new payments this cycle.")

        if args.interval <= 0:
            break
        logger.debug(f"Warte {args.interval}s bis zum nächsten Durchlauf...")
        time.sleep(args.interval)

if __name__ == '__main__':
    main()
