import subprocess

def test_simple_split(tmpdir):
        
    original_list = tmpdir.join('original_list.list')

    with open(str(original_list), 'w') as file:
        for i in range(10):
            file.write('{}\n'.format(i))
    
    subprocess.check_call(["python",
                             "split_dataset.py", 
                             "--input_gammas", original_list.strpath,
                             "--split_gammas", "10", "10", "80",
                             "--output_path", tmpdir.strpath
                             ])

    list1 = tmpdir.join('original_list_TRAINING_ENERGY.list')
    list2 = tmpdir.join('original_list_TRAINING_CLASSIFICATION.list')
    list3 = tmpdir.join('original_list_PERFORMANCE.list')
    
    with open(str(list1), 'r') as file:
        lines_list1 = len(file.readlines())
    with open(str(list2), 'r') as file:
        lines_list2 = len(file.readlines())
    with open(str(list3), 'r') as file:
        lines_list3 = len(file.readlines())
    
    assert lines_list1 == 1
    assert lines_list2 == 1
    assert lines_list3 == 8