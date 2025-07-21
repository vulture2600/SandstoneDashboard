# Using a UNC path
file_path_unc = r"\\SandstoneTS251\Public\Config_Files\config.txt"

# Using a mapped drive letter (if applicable)
#file_path_mapped = r"Z:\folder\filename.txt"

try:
    # Open the file in read mode ('r') using a UNC path
    with open(file_path_unc, 'r') as file:
        content = file.read()
        print("Content from UNC path:")
        print(content)

    # Open the file in read mode ('r') using a mapped drive letter
    # if the share is mapped
    # with open(file_path_mapped, 'r') as file:
    #     content_mapped = file.read()
    #     print("\nContent from mapped drive:")
    #     print(content_mapped)

except FileNotFoundError:
    print(f"Error: The file was not found at the specified path. {file_path_unc}")
except PermissionError:
    print(f"Error: You do not have permission to access the file.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")