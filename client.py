import socket
import sys

# Change the Student IDs in the following line
# Do not change the format
student_id = "[22108336,24202173]"

# to control number of games to play. Matching server, not advised to change
total_game = 10

    # *************************************
    # where you start your code for guessing
    # DO NOT EDIT ANYTHING BEFORE THIS LINE

def guess(rfile, wfile, sock):       # Do NOT change this line

    # Initialize Version Space parameters
    max_p = 200
    max_n_limit = 15000  # Safe upper bound to prevent memory issues
    quantile = 0.50  # Optimal parameter from sandbox analysis

    # Initialize Feasible Set: dictionary mapping 'P' to a set of possible 'N's
    feasible_n_for_p = {p: set(range(1, 1001)) for p in range(1, max_p + 1)}

    while True:
        # 1. Pool all currently possible N values across all valid P's
        all_feasible_n = []
        for p in range(1, max_p + 1):
            all_feasible_n.extend(feasible_n_for_p[p])

        if not all_feasible_n:
            # Absolute failsafe if set collapses completely (should not happen in optimal play)
            my_guess = 500
        else:
            all_feasible_n.sort()

            # 2. Select guess based on the Target Quantile
            target_idx = int(len(all_feasible_n) * quantile)
            if target_idx >= len(all_feasible_n):
                target_idx = len(all_feasible_n) - 1
            my_guess = all_feasible_n[target_idx]

        # 3. Send guess to server
        wfile.write(str(my_guess) + "\n")
        wfile.flush()

        # 4. Read the responses from server
        server_response = rfile.readline().rstrip("\n").rstrip("\r")
        check_code = interpret_server(server_response, sock)

        # 5. Evaluate Response and Update Constraints
        if check_code == 1:
            # Correct! System identified and target found.
            break

        elif check_code == 2:
            # Case 2: Too High (-) -> Eliminate all N >= guess
            for p in range(1, max_p + 1):
                feasible_n_for_p[p] = {n for n in feasible_n_for_p[p] if n < my_guess}

        elif check_code == 3:
            # Case 3: Too Low (+) -> Shift Target
            # Eliminate all N <= guess, then shift survivors right by P
            for p in range(1, max_p + 1):
                new_set = set()
                for n in feasible_n_for_p[p]:
                    if n > my_guess:
                        shifted_n = n + p
                        if shifted_n <= max_n_limit:
                            new_set.add(shifted_n)
                feasible_n_for_p[p] = new_set

    # DO NOT EDIT ANYTHING AFTER THIS LINE
    # where you end your code for guessing
    # ************************************


def interpret_server(server_msg, sock):
    if server_msg == "+":
        print("Guess higher.     ")
        return 3
    elif server_msg == "-":
        print("Guess lower.      ")
        return 2
    elif server_msg == "=":
        print("Correct!")
        return 1
    elif server_msg == "?":
        print("Guess again. You sent something the server doesn't understand.")
        return 0
    else:
        print(f"Server seems not to be respecting the protocol. {server_msg}")
        print("Disconnecting...")
        print("Connection closed. Try again later.")
        sock.close()
        sys.exit(0)




def main():
    serv_addr = "localhost"
    serv_port = 2492

    print("Connecting to server...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((serv_addr, serv_port))
        print("Connection established.")
        print("Trying to communicate...")

        # Use a file-like interface for sending/receiving lines (mirrors Java's BufferedReader/PrintWriter)
        rfile = sock.makefile('r', encoding='utf-8')
        wfile = sock.makefile('w', encoding='utf-8')

        print("Communication established.")
        print("Identification underway...")

        for round_counter in range(1, total_game + 1):
            # Send Group ID to server
            wfile.write(student_id + "\n")
            wfile.flush()

            print("Waiting for the game to start...")
            msg = rfile.readline().rstrip("\n").rstrip("\r")
            if msg != "!":
                print("Server is acting weird. Quitting...")
                rfile.close()
                wfile.close()
                sock.close()
                print("Connection closed. Try again later.")
                sys.exit(0)

            print("Go!")
            input(f"Press enter to start ROUND {round_counter}")

            guess(rfile, wfile, sock)

        print("Thanks for playing, goodbye.")
        print("Disconnecting...")
        wfile.close()
        rfile.close()
        sock.close()
        print("Connection closed.")

    except Exception as e:
        print(f"Connection failed. Try again later. ({e})")

if __name__ == "__main__":
    main()
