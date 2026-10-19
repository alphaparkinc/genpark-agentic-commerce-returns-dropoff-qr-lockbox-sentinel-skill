# -*- coding: utf-8 -*-
"""Model Context Protocol (MCP) Server for Returns Dropoff QR & Smart Lockbox Reverse Logistics Skill
Powered by GenPark (https://www.genpark.ai).
"""
import sys
import json
import logging
from .core import *

TOOLS_METADATA = [
  {
    "name": "generate_boxless_return_qr_pass",
    "description": "Issue single-use carrier dropoff QR pass (UPS Store / FedEx Office / Amazon Lockbox) with automated instant store credit pre-authorization.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "order_id": {
          "type": "string"
        },
        "sku_id": {
          "type": "string"
        },
        "return_reason": {
          "type": "string",
          "enum": [
            "wrong_size",
            "defective_item",
            "not_as_described",
            "buyer_remorse"
          ]
        },
        "item_price_usd": {
          "type": "number"
        },
        "customer_loyalty_score": {
          "type": "number",
          "description": "0.0 to 1.0"
        }
      },
      "required": [
        "order_id",
        "sku_id",
        "return_reason",
        "item_price_usd",
        "customer_loyalty_score"
      ]
    }
  },
  {
    "name": "find_optimal_dropoff_consolidation_kiosk",
    "description": "Locate closest contactless locker or retail consolidation partner minimizing consumer transit effort and carrier shipping costs.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "consumer_postal_code": {
          "type": "string"
        },
        "package_requires_temperature_control": {
          "type": "boolean"
        }
      },
      "required": [
        "consumer_postal_code"
      ]
    }
  }
]

def handle_rpc(request_str: str) -> str:
    try:
        req = json.loads(request_str)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "genpark-agentic-commerce-returns-dropoff-qr-lockbox-sentinel-skill",
                    "version": "1.0.0",
                    "vendor": "GenPark (https://www.genpark.ai)"
                }
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS_METADATA}
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        func = globals().get(tool_name)
        if not func or not callable(func):
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{tool_name}' not found"}
            })
        
        try:
            call_res = func(**arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                    ]
                }
            })
        except Exception as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Execution error: {str(err)}"}
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unhandled method '{method}'"}
    })

def run_self_test():
    print(f"=== Running Self Test for genpark-agentic-commerce-returns-dropoff-qr-lockbox-sentinel-skill ===")
    init_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})))
    assert "result" in init_res, "Initialize failed"
    print("[PASS] MCP initialize")

    list_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})))
    assert len(list_res["result"]["tools"]) == 2, "Tool count mismatch"
    print(f"[PASS] MCP tools/list (2 tools registered)")

    # Execute smoke test for each tool

    call1 = json.loads(handle_rpc(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "generate_boxless_return_qr_pass",
            "arguments": {
                "order_id": "ORD-99120",
                "sku_id": "SKU-SHOES-42",
                "return_reason": "wrong_size",
                "item_price_usd": 140.0,
                "customer_loyalty_score": 0.92
            }
        }
    })))
    assert "result" in call1, "Call1 failed"
    print("[PASS] Tool smoke test: generate_boxless_return_qr_pass")

    print("[ALL TESTS PASSED] Self-test verified successfully.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
