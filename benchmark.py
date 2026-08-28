import time
import random
import string

def generate_random_string(length=4):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def run_benchmark(num_positions, num_watchlist):
    open_positions = [{'symbol': generate_random_string(), 'qty': random.randint(1, 100)} for _ in range(num_positions)]
    watchlist = [generate_random_string() for _ in range(num_watchlist)]

    # Ensure some overlap
    overlap = min(num_positions, num_watchlist) // 2
    for i in range(overlap):
        watchlist[i] = open_positions[i]['symbol']

    random.shuffle(watchlist)

    # Original
    start_time = time.time()
    for _ in range(100): # Run multiple times for better measurement
        for symbol in watchlist:
            existing_pos = next((p for p in open_positions if p['symbol'] == symbol), None)
    end_time = time.time()
    original_time = end_time - start_time

    # Optimized
    start_time = time.time()
    for _ in range(100):
        open_positions_dict = {p['symbol']: p for p in open_positions}
        for symbol in watchlist:
            existing_pos = open_positions_dict.get(symbol)
    end_time = time.time()
    optimized_time = end_time - start_time

    return original_time, optimized_time

if __name__ == "__main__":
    print("Running benchmark...")
    # Using typical portfolio sizes
    num_positions = 500
    num_watchlist = 2000

    original_time, optimized_time = run_benchmark(num_positions, num_watchlist)

    print(f"Original Time: {original_time:.4f} seconds")
    print(f"Optimized Time: {optimized_time:.4f} seconds")
    print(f"Speedup: {original_time / optimized_time:.2f}x")
